# https://github.com/confluentinc/confluent-kafka-python/blob/master/examples/avro_consumer.py
from confluent_kafka import KafkaError, KafkaException, DeserializingConsumer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroDeserializer
from confluent_kafka.serialization import StringDeserializer

import os

from ISR.event_adapters import dict_to_user_image_uploaded_event
from ISR.event_definitions import UserImageUploadedEvent
from ISR.kafka_producer import SharpKafkaProducer
from ISR.utils.logger import get_logger
from ISR.app import predict, destination

running = True
logger = get_logger(__name__)

AVRO_PATH = os.path.join(os.path.dirname(__file__), 'avro')


def __load_user_image_uploaded_schema():
    schema_path = os.path.join(AVRO_PATH, 'user-image-uploaded.avro')

    with open(schema_path) as f:
        return f.read()


def build_avro_deserializer():
    logger.info("building deserializer...")

    sr_conf = {'url': os.environ['KAFKA_SCHEMA_REGISTRY_URL']}
    schema_registry_client = SchemaRegistryClient(sr_conf)

    avro_deserializer = AvroDeserializer(schema_str=__load_user_image_uploaded_schema(),
                                         schema_registry_client=schema_registry_client,
                                         from_dict=dict_to_user_image_uploaded_event)
    logger.info('deserializer created.')
    return avro_deserializer


def build_config():
    string_deserializer = StringDeserializer('utf_8')
    avro_des = build_avro_deserializer()

    return {
        'bootstrap.servers': os.environ['KAFKA_BOOTSTRAP_SERVERS'],
        'group.id': os.environ['KAFKA_CONSUMER_GROUP_ID'],
        'auto.offset.reset': os.environ['KAFKA_CONSUMER_AUTO_OFFSET_RESET'],
        'enable.auto.commit': os.environ['KAFKA_CONSUMER_ENABLE_AUTO_COMMIT'],
        'max.poll.interval.ms': int(os.environ['KAFKA_CONSUMER_MAX_POLL_INTERVAL_MS']),
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


def consume_loop(producer, consumer, topics, process_message):
    try:
        logger.info("subscribing to %s topics..." % topics)
        consumer.subscribe(topics)
        logger.info("subscribed to %s topics..." % topics)
        timeout = os.environ['KAFKA_CONSUMER_POLLING_TIMEOUT_SECONDS']

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
                process_message(msg, producer)
                logger.info("processing function completed. committing offset...")
                consumer.commit(asynchronous=False)
                logger.info("offset committed.")
    finally:
        # Close down consumer to commit final offsets.
        logger.info("closing consumer...")
        consumer.close()
        logger.info("consumer closed.")


def message_processor(msg, producer: SharpKafkaProducer):
    event = msg.value()
    if event is None:
        logger.info("didn't get any event...")
        return

    url = event.url
    logger.info("found url to process %s" % url)
    image_path = process_image(url)
    logger.info("image ready at %s" % image_path)
    processed_bytes = open(image_path, 'rb').read()
    logger.info("producing next event...")
    producer.produce(original_url=url, processed_bytes=processed_bytes)
    logger.info("event produced. message processed.")


def process_image(url):
    logger.info("received url %s" % url)
    filepath = destination()
    model_name = os.environ['MODEL_NAME']
    by_patch_of_size = int(os.environ['MODEL_BY_PATCH_OF_SIZE'])
    batch_size = int(os.environ['MODEL_BATCH_SIZE'])
    padding_size = int(os.environ['MODEL_PADDING_SIZE'])
    logger.info("running prediction")
    predict(url, model_name, filepath, by_patch_of_size, batch_size, padding_size)
    return filepath


if __name__ == "__main__":
    logger.info("starting app...")
    # process_image('https://jimdo-storage.freetls.fastly.net/image/188163642/dda9a2c3-f1a1-49e8-a773-d66051733cd9.jpg')

    kafka_topics = os.environ['KAFKA_TOPIC_USER_IMAGE_TO_PROCESS'].split(',')
    kafka_consumer = create_consumer()
    kafka_producer = SharpKafkaProducer(topic=os.environ['KAFKA_TOPIC_USER_IMAGE_PROCESSED'])
    consume_loop(kafka_producer, kafka_consumer, kafka_topics, message_processor)
