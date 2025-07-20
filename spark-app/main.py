#!/usr/bin/env python3
"""
Conway's Game of Life - PySpark Implementation with Kafka Integration

This program simulates Conway's Game of Life using PySpark for distributed computation.
It listens to a Kafka topic for simulation parameters and sends results back to Kafka.
"""

import time
import json
import os
import uuid
import numpy as np
from pyspark import SparkConf
from pyspark.sql import SparkSession
from kafka import KafkaConsumer, KafkaProducer

# Configure logging
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# Suppress only the noisy Kafka operational logs
logging.getLogger("kafka.coordinator.heartbeat").setLevel(logging.ERROR)
logging.getLogger("kafka.coordinator.consumer").setLevel(logging.ERROR)
logging.getLogger("kafka.coordinator").setLevel(logging.ERROR)

KAFKA_BROKER = os.environ.get("KAFKA_BROKER", "localhost:9092")
TOPIC_IN = os.environ.get("TOPIC_IN", "jogo-da-vida-spark")
TOPIC_OUT = os.environ.get("TOPIC_OUT", "jogo-da-vida-output")
GROUP_ID = os.environ.get("GROUP_ID", "spark-jogo-da-vida-group")

logger = logging.getLogger(__name__)


def get_neighbors(row, col):
    """Get the coordinates of the 8 neighboring cells."""
    return [
        (row - 1, col - 1),
        (row - 1, col),
        (row - 1, col + 1),
        (row, col - 1),
        (row, col + 1),
        (row + 1, col - 1),
        (row + 1, col),
        (row + 1, col + 1),
    ]


def emit_signals(cell):
    """Emit cell state and neighbor signals."""
    (coords, state) = cell
    row, col = coords
    signals = []

    # Only live cells emit neighbor signals
    if state == 1:
        for neighbor_coords in get_neighbors(row, col):
            signals.append((neighbor_coords, "NEIGHBOR"))

    # Always emit the cell itself
    signals.append((coords, state))
    return signals


def count_neighbors(signals):
    """Count neighbors from signals."""
    live = 0
    neighbors = 0

    for s in signals:
        if s == "NEIGHBOR":
            neighbors += 1
        elif s == 1:
            live = 1

    return (live, neighbors)


def apply_rules(cell_data, board_size):
    """Apply Game of Life rules to determine next cell state."""
    coords, (state, neighbors) = cell_data
    row, col = coords

    # Skip border cells
    if row == 0 or row == board_size + 1 or col == 0 or col == board_size + 1:
        return (coords, 0)

    # Apply Conway's Game of Life rules
    if state == 1 and (neighbors < 2 or neighbors > 3):
        # Rule 1 & 3: Underpopulation or overpopulation
        return (coords, 0)
    elif state == 0 and neighbors == 3:
        # Rule 4: Reproduction
        return (coords, 1)
    else:
        # Rule 2: Survival or remain dead
        return (coords, state)


def initialize_board(sc, size):
    """Initialize the board with a glider pattern."""
    # Initialize all cells to dead (0)
    cells = []
    for i in range(size + 2):
        for j in range(size + 2):
            cells.append(((i, j), 0))

    # Set the glider pattern
    glider_cells = [((1, 2), 1), ((2, 3), 1), ((3, 1), 1), ((3, 2), 1), ((3, 3), 1)]

    # Replace the dead cells with live ones for the glider
    for gc in glider_cells:
        idx = (gc[0][0] * (size + 2)) + gc[0][1]
        cells[idx] = gc

    # Create an RDD from the cells
    return sc.parallelize(cells)


def evolve_board(board, board_size, iteration=0, checkpoint_interval=5):
    """Evolve the board to the next generation."""
    # Step 1: For each cell, emit its neighbors to count them
    all_signals = board.flatMap(emit_signals)

    # Step 2: Group by coordinates and count neighbors
    cell_with_neighbors = all_signals.groupByKey().mapValues(list).mapValues(count_neighbors)

    # Step 3: Apply Game of Life rules
    result = cell_with_neighbors.map(lambda x: apply_rules(x, board_size))

    # Checkpoint periodically to truncate RDD lineage and avoid stack overflow
    if iteration > 0 and iteration % checkpoint_interval == 0:
        result.checkpoint()
        # Force evaluation to materialize the checkpoint
        result.count()

    return result


def board_to_array(board, size):
    """Convert board RDD to NumPy array."""
    # Collect the RDD to a list and convert to a 2D array
    collected_cells = board.collect()

    # Create an empty 2D array
    board_array = np.zeros((size + 2, size + 2), dtype=np.int8)

    # Fill the array with the values from collected cells
    for (row, col), state in collected_cells:
        board_array[row, col] = state

    return board_array


def is_correct(board_array, size):
    """Check if the board has the expected final state."""
    # Check if the glider has reached the bottom-right corner correctly
    i, j = size, size
    total_alive = np.sum(board_array)

    # The glider pattern at the bottom-right corner should be:
    #   .X.
    #   ..X
    #   XXX
    return (
        total_alive == 5
        and board_array[i - 2, j - 1] == 1
        and board_array[i - 1, j] == 1
        and board_array[i, j - 2] == 1
        and board_array[i, j - 1] == 1
        and board_array[i, j] == 1
    )


def send_log(producer, topic, log_message):
    """Send a log message to Kafka."""
    # Don't modify the log message here - we'll handle it in run_simulation
    producer.send(topic, log_message.encode("utf-8"))


def run_simulation(
    size_power,
    spark,
    kafka_producer,
    log_topic,
    game_id,
    current_step,
    total_steps,
    step_start_time,
    checkpoint_interval=5,
):
    """Run the Game of Life simulation for a specified board size."""
    size = 1 << size_power  # Calculate board size as 2^power
    sc = spark.sparkContext

    simulation_id = f"sim_{size_power}_{int(time.time())}"

    # Set up checkpointing directory if it doesn't exist
    checkpoint_dir = f"./checkpoint_dir_{size}_{simulation_id}"
    if not os.path.exists(checkpoint_dir):
        os.makedirs(checkpoint_dir)
    sc.setCheckpointDir(checkpoint_dir)

    # Initialize the board
    t0 = time.time()
    board = initialize_board(sc, size)
    t1 = time.time()

    # Run the simulation
    # We need 4*(size-3) iterations to ensure glider reaches corner
    iterations_needed = 4 * (size - 3)

    for i in range(iterations_needed):
        # Pass iteration number to evolve_board for checkpointing
        board = evolve_board(board, size, i, checkpoint_interval)

    t2 = time.time()

    # Collect final board and check if it's correct
    final_array = board_to_array(board, size)
    correct = is_correct(final_array, size)
    result_str = "CORRETO" if correct else "ERRADO"

    t3 = time.time()

    # Calculate timing
    init_time = t1 - t0
    computation_time = t2 - t1
    verification_time = t3 - t2
    total_time = t3 - t0

    # Record step end time
    step_end_time = int(time.time())

    # Create JSON message matching OpenMP app schema
    json_line = {
        "game_id": game_id,
        "step": current_step,
        "total_steps": total_steps,
        "board_size": size,
        "start_time": step_start_time,
        "end_time": step_end_time,
        "impl": "spark",
    }

    # Send the telemetry data as JSON
    kafka_producer.send(log_topic, value=json.dumps(json_line))
    logger.info(f"[*] Telemetria enviada: {json_line}")

    # Print log to console with timing details for debugging
    log_msg = (
        f"tam={size}; tempos: init={init_time:7.7f}, comp={computation_time:7.7f}, "
        f"fim={verification_time:7.7f}, tot={total_time:7.7f}; resultado={result_str}"
    )
    logger.info(log_msg)

    # Clean up checkpoint directory
    import shutil

    if os.path.exists(checkpoint_dir):
        shutil.rmtree(checkpoint_dir)

    return correct, (init_time, computation_time, verification_time, total_time)


def kafka_consumer_loop(spark):
    """Main loop that listens to Kafka for simulation requests."""
    logger.info("Starting application with config:")
    logger.info(f"  KAFKA_BROKER: {KAFKA_BROKER}")
    logger.info(f"  TOPIC_IN: {TOPIC_IN}")
    logger.info(f"  TOPIC_OUT: {TOPIC_OUT}")
    logger.info(f"  GROUP_ID: {GROUP_ID}")

    # Initialize Kafka consumer
    consumer = KafkaConsumer(
        TOPIC_IN,
        bootstrap_servers=[KAFKA_BROKER],
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        group_id=GROUP_ID,
        value_deserializer=lambda x: json.loads(x.decode("utf-8")),
    )

    # Initialize Kafka producer with JSON serializer to match OpenMP app
    producer = KafkaProducer(bootstrap_servers=[KAFKA_BROKER], value_serializer=lambda x: x.encode("utf-8"))

    logger.info(f"Consumidor conectado ao broker '{KAFKA_BROKER}' e inscrito no tópico '{TOPIC_IN}'")

    # Main loop - consume messages and run simulations
    try:
        for message in consumer:
            try:
                # Extract message data - should be JSON with powmin and powmax (like OpenMP app)
                value = message.value
                logger.info(f"[*] Mensagem recebida: {value}")

                powmin = value["powmin"]
                powmax = value["powmax"]

                # Generate unique game ID for this execution
                game_id = str(uuid.uuid4())
                total_steps = powmax - powmin + 1
                current_step = 0

                # Record when we start the entire process
                process_start_time = int(time.time())
                step_start_time = process_start_time

                logger.info(f"Received request: powmin={powmin}, powmax={powmax}")

                # Run simulations for each power in the range
                for power in range(powmin, powmax + 1):
                    current_step += 1
                    logger.info(f"Starting simulation for board size 2^{power} = {1 << power}")

                    # Default checkpoint interval - adjust based on board size
                    checkpoint_interval = max(2, min(10, (1 << power) // 16))

                    # Run simulation with current power
                    run_simulation(
                        power,
                        spark,
                        producer,
                        TOPIC_OUT,
                        game_id,
                        current_step,
                        total_steps,
                        step_start_time,
                        checkpoint_interval,
                    )

                    # Next step starts when this one ends
                    step_start_time = int(time.time())

                producer.flush()

            except Exception as e:
                # Log error
                error_msg = f"ERROR: {str(e)}"
                logger.error(error_msg)
                send_log(producer, TOPIC_OUT, error_msg)

    except KeyboardInterrupt:
        logger.info("Consumidor encerrado.")
    finally:
        consumer.close()
        producer.close()


def main():
    """Main function to initialize Spark and start Kafka consumer."""
    logger.info("Starting Spark Game of Life application")

    # Initialize Spark with appropriate configuration
    conf = SparkConf().setAppName("Game of Life Spark")

    # Check if running in Kubernetes
    if "KUBERNETES_SERVICE_HOST" in os.environ:
        # Running in Kubernetes - Spark will handle distribution automatically
        logger.info("Detected Kubernetes environment - using distributed Spark")
        # Don't set master here - let Spark handle it based on deployment
    else:
        # Running locally for development
        logger.info("Running in local mode for development")
        conf.setMaster("local[*]")  # Use all available cores locally

    # Configure Spark for better performance
    conf.set("spark.ui.showConsoleProgress", "false")
    conf.set("spark.executor.memory", "2g")
    conf.set("spark.driver.memory", "2g")

    spark = SparkSession.builder.config(conf=conf).getOrCreate()
    spark.sparkContext.setLogLevel("ERROR")  # Reduce logging

    try:
        # Start the Kafka consumer loop
        kafka_consumer_loop(spark)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        # Stop the Spark session when done
        spark.stop()


if __name__ == "__main__":
    main()
