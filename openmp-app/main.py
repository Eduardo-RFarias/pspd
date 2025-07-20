import os
import subprocess
import json
import logging
from typing import IO, cast
from kafka import KafkaConsumer, KafkaProducer

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

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
                        # Parse format: tam=8, tempos: init=0.0000031, comp=0.0012369, fim=0.0000050, tot=0.0012450
                        parts = line.split(", ")

                        # Extract tam value
                        tam_part = parts[0]  # "tam=8"
                        tam = int(tam_part.split("=")[1])

                        # Extract timing values from "tempos: init=X, comp=Y, fim=Z, tot=W"
                        tempos_part = ", ".join(
                            parts[1:]
                        )  # "tempos: init=0.0000031, comp=0.0012369, fim=0.0000050, tot=0.0012450"
                        tempos_part = tempos_part.replace(
                            "tempos: ", ""
                        )  # "init=0.0000031, comp=0.0012369, fim=0.0000050, tot=0.0012450"

                        timing_pairs = tempos_part.split(", ")
                        timings = {}
                        for pair in timing_pairs:
                            key, value = pair.split("=")
                            timings[key] = float(value)

                        json_line = {
                            "tam": tam,
                            "init": timings["init"],
                            "comp": timings["comp"],
                            "fim": timings["fim"],
                            "tot": timings["tot"],
                        }

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
