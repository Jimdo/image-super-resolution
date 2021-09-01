# https://github.com/confluentinc/confluent-kafka-python/blob/master/examples/avro_consumer.py
from datetime import datetime
from time import time

from confluent_kafka import KafkaError, KafkaException, DeserializingConsumer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroDeserializer
from confluent_kafka.serialization import StringDeserializer

import os
import hashlib
import boto3

from ISR.event_adapters import dict_to_user_image_uploaded_event
from ISR.event_definitions import ImageSuperResolutionImageProcessedEvent
from ISR.kafka_producer import SharpKafkaProducer
from ISR.utils.logger import get_logger
from ISR.app import get_processing_configuration, process_image

running = True
logger = get_logger(__name__)

AVRO_PATH = os.path.join(os.path.dirname(__file__), 'avro')


def __load_user_image_uploaded_schema():
    # Please notice that this schema is used by the one specified in
    # image-super-resolution-processed-image.avro
    # I was unable to load both schemas and reference one from the other.
    # So if you make changes to the user-iamge-uploaded.avro schema
    # please update the other schema.
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
    bucket = None
    object_key = None

    logger.info("found url to process %s" % url)
    start = time()
    image_path = process_image(url)
    end = time()
    processing_time_in_ms = int((end - start) * 1000)

    if image_path is None:
        logger.warn("unable to process image")

    if image_path is not None:
        logger.info("image ready at %s" % image_path)

        object_key = hashlib.md5(url.encode()).hexdigest()
        bucket = os.environ['PROCESSED_IMAGES_BUCKET']
        logger.info("uploading image to s3://{}/{}...".format(bucket, object_key))
        store_image(image_path, bucket, object_key)
        logger.info("producing next event...")

    user_image_processed_event = ImageSuperResolutionImageProcessedEvent(
        original_url=url, bucket=bucket, object_key=object_key,
        processing_time_in_ms=processing_time_in_ms,
        created_at=datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        user_image=event, processing_configuration=get_processing_configuration(),
        success=image_path is not None
    )
    producer.produce(user_image_processed_event)
    logger.info("event produced. message processed.")


def store_image(image_path, bucket, object_key):
    s3 = boto3.resource('s3')
    with open(image_path, "rb") as data:
        s3.Bucket(bucket).put_object(Key=object_key, Body=data)


if __name__ == "__main__":
    logger.info("starting app...")
    # process_image('https://jimdo-storage.freetls.fastly.net/image/188163642/dda9a2c3-f1a1-49e8-a773-d66051733cd9.jpg')

    kafka_topics = os.environ['KAFKA_TOPIC_USER_IMAGE_TO_PROCESS'].split(',')
    kafka_consumer = create_consumer()
    kafka_producer = SharpKafkaProducer(topic=os.environ['KAFKA_TOPIC_USER_IMAGE_PROCESSED'])
    consume_loop(kafka_producer, kafka_consumer, kafka_topics, message_processor)
