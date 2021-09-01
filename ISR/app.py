import os
from importlib import import_module
from pathlib import Path
from time import time
from urllib.error import URLError

import imageio
import yaml
import string

from ISR.event_definitions import ImageSuperResolutionConfiguration
from ISR.utils.logger import get_logger
from ISR.utils.utils import get_timestamp, get_config_from_weights
import random


def _get_module(generator):
    return import_module('ISR.models.' + generator)


def is_gpu():
    return os.environ['HOST_MODE'] == 'GPU'


logger = get_logger(__name__)
logger.info('Started in ' + ('GPU' if is_gpu() else 'CPU') + ' mode')


def get_processing_configuration():
    return ImageSuperResolutionConfiguration(
        model_name=os.environ['MODEL_NAME'],
        by_patch_of_size=int(os.environ['MODEL_BY_PATCH_OF_SIZE']),
        batch_size=int(os.environ['MODEL_BATCH_SIZE']),
        padding_size=int(os.environ['MODEL_PADDING_SIZE'])
    )


def _setup_model(model):
    # Available Models
    # RDN: psnr-large, psnr-small, noise-cancel
    # RRDN: gans
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
    config_file = 'config.yml'
    conf = yaml.load(open(config_file, 'r'), Loader=yaml.FullLoader)

    lr_patch_size = conf['session']['prediction']['patch_size']
    generator_name = conf['models'][model]['generator']
    weights_path = conf['models'][model]['weights_path']
    logger.info('Model {}\n Generator {}\n Weights\n {}'.format(model, generator_name, weights_path))
    params = get_config_from_weights(
        weights_path, conf['generators'][generator_name], generator_name
    )

    module = _get_module(generator_name)
    gen = module.make_model(params, lr_patch_size)
    gen.model.load_weights(str(weights_path))
    return gen


def destination():
    output_dir = Path('./data/output') / get_timestamp()
    output_dir.mkdir(parents=True, exist_ok=True)
    name = ''.join(random.choices(string.ascii_uppercase, k=5))
    output_path = output_dir / (name + '.jpg')
    return output_path


model = _setup_model(os.environ['MODEL_NAME'])


def process_image(url):
    logger.info('Downloading file\n > {}'.format(url))
    try:
        img = imageio.imread(url)
    except URLError:
        logger.info('Could not download the file.')
        return None

    processing_configuration = get_processing_configuration()
    logger.info('size: {}x{}'.format(img.shape[1], img.shape[0]))
    logger.info('by_patch_of_size: {}'.format(processing_configuration.by_patch_of_size))
    logger.info('batch_size: {}'.format(processing_configuration.batch_size))
    logger.info('padding_size: {}'.format(processing_configuration.padding_size))
    destination_path = destination()
    logger.info('Result will be saved in\n > {}'.format(destination_path))
    start = time()
    sr_img = model.predict(img,
                           by_patch_of_size=processing_configuration.by_patch_of_size,
                           batch_size=processing_configuration.batch_size,
                           padding_size=processing_configuration.padding_size)
    end = time()
    logger.info('Elapsed time: {}s'.format(end - start))
    imageio.imwrite(destination_path, sr_img)
    return destination_path
