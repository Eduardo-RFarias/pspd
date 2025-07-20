import os
import subprocess
import json
import logging
import uuid
import time
from typing import IO, cast
from kafka import KafkaConsumer, KafkaProducer

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# Suppress only the noisy Kafka operational logs
logging.getLogger("kafka.coordinator.heartbeat").setLevel(logging.ERROR)
logging.getLogger("kafka.coordinator.consumer").setLevel(logging.ERROR)
logging.getLogger("kafka.coordinator").setLevel(logging.ERROR)

KAFKA_BROKER = os.environ.get("KAFKA_BROKER", "localhost:9092")
TOPIC_IN = os.environ.get("TOPIC_IN", "jogo-da-vida")
TOPIC_OUT = os.environ.get("TOPIC_OUT", "jogo-da-vida-output")
GROUP_ID = os.environ.get("GROUP_ID", "jogo-da-vida-group")

logger = logging.getLogger(__name__)


def main():
    logger.info("Starting application with config:")
    logger.info(f"  KAFKA_BROKER: {KAFKA_BROKER}")
    logger.info(f"  TOPIC_IN: {TOPIC_IN}")
    logger.info(f"  TOPIC_OUT: {TOPIC_OUT}")
    logger.info(f"  GROUP_ID: {GROUP_ID}")

    consumer = KafkaConsumer(
        TOPIC_IN,
        bootstrap_servers=[KAFKA_BROKER],
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        group_id=GROUP_ID,
        value_deserializer=lambda x: json.loads(x.decode("utf-8")),
    )

    producer = KafkaProducer(bootstrap_servers=[KAFKA_BROKER], value_serializer=lambda x: x.encode("utf-8"))

    logger.info(f"Consumidor conectado ao broker '{KAFKA_BROKER}' e inscrito no tópico '{TOPIC_IN}'")

    try:
        for message in consumer:
            value = message.value
            logger.info(f"[*] Mensagem recebida: {value}")

            try:
                powmin = value["powmin"]
                powmax = value["powmax"]

                # Generate unique game ID for this execution
                game_id = str(uuid.uuid4())
                total_steps = powmax - powmin + 1
                current_step = 0

                # Record when we start the entire process
                process_start_time = int(time.time())
                step_start_time = process_start_time

                process = subprocess.Popen(
                    ["./jogodavida_openmp", str(powmin), str(powmax)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )

                logger.info("[*] Resultado da execução:")

                # Real-time stdout reading
                for line in iter(cast(IO[str], process.stdout).readline, ""):
                    line = line.strip()
                    logger.info(line)

                    if line.startswith("tam"):
                        current_step += 1

                        # Record step end time
                        step_end_time = int(time.time())

                        # Parse format: tam=8, tempos: init=0.0000031, comp=0.0012369, fim=0.0000050, tot=0.0012450
                        parts = line.split(", ")

                        # Extract tam value
                        tam_part = parts[0]  # "tam=8"
                        board_size = int(tam_part.split("=")[1])

                        json_line = {
                            "game_id": game_id,
                            "step": current_step,
                            "total_steps": total_steps,
                            "board_size": board_size,
                            "start_time": step_start_time,
                            "end_time": step_end_time,
                            "impl": "openmp",
                        }

                        # Next step starts when this one ends
                        step_start_time = step_end_time

                        producer.send(TOPIC_OUT, value=json.dumps(json_line))
                        logger.info(f"[*] Telemetria enviada: {json_line}")

                producer.flush()

                # Error handling
                stderr = process.communicate()[1]
                if stderr:
                    logger.error(f"[!] Erro na execução: {stderr}")

            except (KeyError, subprocess.CalledProcessError) as e:
                logger.error(f"[!] Erro ao processar a mensagem: {e}")

    except KeyboardInterrupt:
        logger.info("Consumidor encerrado.")
    finally:
        consumer.close()
        producer.close()


if __name__ == "__main__":
    main()
