# https://github.com/confluentinc/confluent-kafka-python/blob/master/examples/avro_consumer.py

from confluent_kafka import KafkaError, KafkaException, DeserializingConsumer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroDeserializer
from confluent_kafka.serialization import StringDeserializer

import os

from ISR.utils.logger import get_logger
from ISR.app import predict, destination

running = True
logger = get_logger(__name__)


def build_avro_deserializer():
    logger.info("building deserializer...")
    schema_str = """
    {
        "name": "user_image_uploaded_event",
        "type": "record",
        "fields": [
            {"name": "url", "type": "string"}
        ]
    }
    """

    sr_conf = {'url': os.environ['KAFKA_SCHEMA_REGISTRY']}
    schema_registry_client = SchemaRegistryClient(sr_conf)

    avro_deserializer = AvroDeserializer(schema_str=schema_str,
                                         schema_registry_client=schema_registry_client,
                                         from_dict=dict_to_event)
    logger.info('deserializer created.')
    return avro_deserializer


class UserImageUploadedEvent(object):
    """
    UserImageUploadedEvent record
    Args:
        url (str): url to access the image
    """
    def __init__(self, url=None):
        self.url = url


def dict_to_event(obj, ctx):
    """
    Converts object literal(dict) to a User instance.
    Args:
        obj (dict): Object literal(dict)
        ctx (SerializationContext): Metadata pertaining to the serialization
            operation.
    """
    if obj is None:
        return None

    logger.info('building event with url %s' % obj['url'])
    return UserImageUploadedEvent(url=obj['url'])


def build_config():
    servers = os.environ['KAFKA_BOOTSTRAP_SERVERS']
    group_id = os.environ['KAFKA_GROUP_ID']
    auto_offset_reset = os.environ['KAFKA_AUTO_OFFSET_RESET']
    enable_auto_commit = os.environ['KAFKA_ENABLE_AUTO_COMMIT']

    string_deserializer = StringDeserializer('utf_8')
    avro_des = build_avro_deserializer()

    return {
        'bootstrap.servers': servers,
        'group.id': group_id,
        'auto.offset.reset': auto_offset_reset,
        'enable.auto.commit': enable_auto_commit,
        'key.deserializer': string_deserializer,
        'value.deserializer': avro_des,
    }


def shutdown():
    logger.info("shutdown requested")
    global running
    running = False


def create_consumer():
    config = build_config()
    logger.info("creating consumer with config")
    logger.info(config)
    new_consumer = DeserializingConsumer(config)
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
    event = msg.value()
    if event is None:
        logger.info("didn't get any event...")
        return

    url = event.url
    logger.info("received url %s" % url)
    filepath = destination()

    model_name = os.environ['MODEL_NAME']
    by_patch_of_size = int(os.environ['MODEL_BY_PATCH_OF_SIZE'])
    batch_size = int(os.environ['MODEL_BATCH_SIZE'])
    padding_size = int(os.environ['MODEL_PADDING_SIZE'])

    logger.info("running prediction")
    predict(url, model_name, filepath, by_patch_of_size, batch_size, padding_size)


if __name__ == "__main__":
    logger.info("starting app...")
    kafka_topics = os.environ['KAFKA_TOPICS'].split(',')
    kafka_consumer = create_consumer()
    consume_loop(kafka_consumer, kafka_topics, message_processor)
