import sys

from confluent_kafka import Consumer, KafkaError, KafkaException
import os

from ISR.utils.logger import get_logger
from ISR.app import predict, destination

running = True
logger = get_logger(__name__)


def build_config():
    servers = os.environ['KAFKA_BOOTSTRAP_SERVERS']
    group_id = os.environ['KAFKA_GROUP_ID']
    auto_offset_reset = os.environ['KAFKA_AUTO_OFFSET_RESET']
    enable_auto_commit = os.environ['KAFKA_ENABLE_AUTO_COMMIT']

    return {
        'bootstrap.servers': servers,
        'group.id': group_id,
        'auto.offset.reset': auto_offset_reset,
        'enable.auto.commit': enable_auto_commit
    }


def shutdown():
    logger.info("shutdown requested")
    global running
    running = False


def create_consumer():
    config = build_config()
    logger.info("creating consumer with config")
    logger.info(config)
    new_consumer = Consumer(config)
    logger.info("consumer created")
    return new_consumer


def consume_loop(consumer, topics, process_message):
    try:
        logger.info("subscribing to %s topics..." % topics)
        consumer.subscribe(topics)
        logger.info("subscribed to %s topics..." % topics)
        timeout = os.environ['KAFKA_POLLING_TIMEOUT_SECONDS']

        while running:
            logger.info("polling with %ss timeout..." % timeout)
            msg = consumer.poll(timeout=float(timeout))
            if msg is None:
                logger.info("no messages found.")
                continue

            if msg.error():
                logger.warn("message contains an error.")
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    # End of partition event
                    logger.error('%% %s [%d] reached end at offset %d\n' %
                                 (msg.topic(), msg.partition(), msg.offset()))
                elif msg.error():
                    raise KafkaException(msg.error())
            else:
                logger.info("message received. calling processing function...")
                process_message(msg)
                logger.info("processing function completed. committing offset...")
                consumer.commit(asynchronous=False)
                logger.info("offset committed.")
    finally:
        # Close down consumer to commit final offsets.
        logger.info("closing consumer...")
        consumer.close()
        logger.info("consumer closed.")


def message_processor(msg):
    url = msg.image.url
    filepath = destination()

    model_name = os.environ['MODEL_NAME']
    by_patch_of_size = os.environ['MODEL_BY_PATCH_OF_SIZE']
    batch_size = os.environ['MODEL_BATCH_SIZE']
    padding_size = os.environ['MODEL_PADDING_SIZE']

    logger.info("running prediction")
    predict(url, model_name, filepath, by_patch_of_size, batch_size, padding_size)


if __name__ == "__main__":
    logger.info("starting app...")
    kafka_topics = os.environ['KAFKA_TOPICS'].split(',')
    kafka_consumer = create_consumer()
    consume_loop(kafka_consumer, kafka_topics, message_processor)
