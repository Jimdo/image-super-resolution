# https://github.com/confluentinc/confluent-kafka-python/blob/master/examples/avro_producer.py
# https://towardsdatascience.com/kafka-in-action-building-a-distributed-multi-video-processing-pipeline-with-python-and-confluent-9f133858f5a0
from uuid import uuid4

from confluent_kafka import SerializingProducer
from confluent_kafka.serialization import StringSerializer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer

from ISR.event_adapters import user_image_processed_event_to_dict
from ISR.event_definitions import ImageSuperResolutionImageProcessedEvent
from ISR.utils.logger import get_logger

import os

logger = get_logger(__name__)

AVRO_PATH = os.path.join(os.path.dirname(__file__), 'avro')


def __load_schemas():
    # Please notice that the schema has a property called user_image
    # that property is a copy of the schema specified in user-image-uploaded.avro
    # I was unable to load both schemas and reference one from the other.
    schema_path = os.path.join(AVRO_PATH, 'image-super-resolution-processed-image.avro')
    with open(schema_path) as f:
        return f.read()


def build_avro_serializer():
    logger.info("building serializer...")

    sr_conf = {'url': os.environ['KAFKA_SCHEMA_REGISTRY_URL']}
    schema_registry_client = SchemaRegistryClient(sr_conf)

    avro_serializer = AvroSerializer(schema_str=__load_schemas(),
                                     schema_registry_client=schema_registry_client,
                                     to_dict=user_image_processed_event_to_dict)
    logger.info('serializer created.')
    return avro_serializer


def build_config():
    string_serializer = StringSerializer('utf_8')
    avro_ser = build_avro_serializer()

    return {
        'bootstrap.servers': os.environ['KAFKA_BOOTSTRAP_SERVERS'],
        'key.serializer': string_serializer,
        'value.serializer': avro_ser,
    }


def create_producer():
    config = build_config()
    logger.info("creating producer with config")
    logger.info(config)
    new_producer = SerializingProducer(config)
    logger.info("producer created")
    return new_producer


def delivery_report(err, msg):
    """
    Reports the failure or success of a message delivery.
    Args:
        err (KafkaError): The error that occurred on None on success.
        msg (Message): The message that was produced or failed.
    Note:
        In the delivery report callback the Message.key() and Message.value()
        will be the binary format as encoded by any configured Serializers and
        not the same object that was passed to produce().
        If you wish to pass the original object(s) for key and value to delivery
        report callback we recommend a bound callback or lambda where you pass
        the objects along.
    """
    if err is not None:
        logger.info("Delivery failed for UserImageProcessedEvent record {}: {}".format(msg.key(), err))
        return
    logger.info('UserImageProcessedEvent record {} successfully produced to {} [{}] at offset {}'.format(
        msg.key(), msg.topic(), msg.partition(), msg.offset()))


class SharpKafkaProducer:
    def __init__(self, topic):
        logger.info('creating producer...')
        self.producer = create_producer()
        logger.info('producer created.')
        self.topic = topic

    def produce(self, user_image_processed_event):
        logger.info('producing record...')
        logger.info(user_image_processed_event_to_dict(user_image_processed_event, None))
        try:
            self.producer.produce(topic=self.topic, key=str(uuid4()),
                                  value=user_image_processed_event,
                                  on_delivery=delivery_report)
            # Trigger on_delivery callbacks from previous calls to produce()
            self.producer.poll(0.0)
            # Flush event. In this use case we don't need to batch before sending them
            self.producer.flush()
        except ValueError:
            logger.error("Invalid event, discarding...")
