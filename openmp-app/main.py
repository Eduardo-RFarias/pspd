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
                        line = [kv.strip() for kv in line.split(",")]

                        json_line = {
                            "tam": int(line[1]),
                            "init": float(line[2]),
                            "comp": float(line[3]),
                            "fim": float(line[4]),
                            "tot": float(line[5]),
                        }

                        producer.send(TOPIC_OUT, value=json.dumps(json_line))

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
