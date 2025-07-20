import os
import json
import logging
from kafka import KafkaConsumer
from elasticsearch import Elasticsearch
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

KAFKA_BROKER = os.environ.get("KAFKA_BROKER", "localhost:9092")
TOPIC_IN = os.environ.get("TOPIC_IN", "jogo-da-vida-output")
ELASTICSEARCH_HOST = os.environ.get("ELASTICSEARCH_HOST", "localhost:9200")
ELASTICSEARCH_INDEX = os.environ.get("ELASTICSEARCH_INDEX", "jogo-da-vida-telemetry")

logger = logging.getLogger(__name__)


def main():
    logger.info("Starting application with config:")
    logger.info(f"  KAFKA_BROKER: {KAFKA_BROKER}")
    logger.info(f"  TOPIC_IN: {TOPIC_IN}")
    logger.info(f"  ELASTICSEARCH_HOST: {ELASTICSEARCH_HOST}")
    logger.info(f"  ELASTICSEARCH_INDEX: {ELASTICSEARCH_INDEX}")

    consumer = KafkaConsumer(
        TOPIC_IN,
        bootstrap_servers=[KAFKA_BROKER],
        auto_offset_reset="earliest",
        group_id="elasticsearch-consumer-group",
        value_deserializer=lambda x: json.loads(x.decode("utf-8")),
    )

    es = Elasticsearch([ELASTICSEARCH_HOST])

    logger.info(f"Consumidor conectado ao broker '{KAFKA_BROKER}' e inscrito no tópico '{TOPIC_IN}'")

    for message in consumer:
        value = message.value
        logger.info(f"[*] Mensagem recebida: {value}")

        # Add timestamp and send to Elasticsearch
        doc = {**value, "timestamp": datetime.utcnow().isoformat()}

        es.index(index=ELASTICSEARCH_INDEX, body=doc)
        logger.info(f"[*] Enviado para Elasticsearch: {doc}")


if __name__ == "__main__":
    main()
