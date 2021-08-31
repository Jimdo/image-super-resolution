import os
from importlib import import_module
from pathlib import Path
from time import time
import imageio
import yaml
import string
from ISR.utils.logger import get_logger
from ISR.utils.utils import get_timestamp, get_config_from_weights
import random


def check_origin(url):
    valid_origins = [
        'jimdo-dolphin-static-assets-stage.freetls.fastly.net',
        'content-storage-stage.freetls.fastly.net',
        'jimdo-dolphin-static-assets-prod.freetls.fastly.net',
        'jimdo-storage.freetls.fastly.net',
        'jimdo-dolphin-static-assets-stage.freetls.fastly.net',
        'content-storage-stage.freetls.fastly.net'
    ]
    origin = url.split('/')[2]
    return origin in valid_origins


def _get_module(generator):
    return import_module('ISR.models.' + generator)


def is_gpu():
    return os.environ['HOST_MODE'] == 'GPU'


logger = get_logger(__name__)
logger.info('Started in ' + ('GPU' if is_gpu() else 'CPU') + ' mode')


def predict(url, destination_path, model_name, by_patch_of_size, batch_size, padding_size):
    physical_devices = []
    if is_gpu():
        import tensorflow as tf
        physical_devices = tf.config.list_physical_devices('GPU')
        tf.config.experimental.set_memory_growth(physical_devices[0], True)

    logger.info("Num GPUs Available: {}".format(len(physical_devices)))
    logger.info('Magnifying with {}'.format(model_name))
    gen = _setup_model(model_name)
    run(url, gen, destination_path, by_patch_of_size, batch_size, padding_size)


def _setup_model(model):
    # Available Models
    # RDN: psnr-large, psnr-small, noise-cancel
    # RRDN: gans
    logger = get_logger(__name__)
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


def run(url, gen, destination_path, by_patch_of_size, batch_size, padding_size):
    logger.info('Downloading file\n > {}'.format(url))
    img = imageio.imread(url)
    logger.info('size: {}x{}'.format(img.shape[1], img.shape[0]))
    logger.info('by_patch_of_size: {}'.format(by_patch_of_size))
    logger.info('batch_size: {}'.format(batch_size))
    logger.info('padding_size: {}'.format(padding_size))
    logger.info('Result will be saved in\n > {}'.format(destination_path))
    start = time()
    sr_img = gen.predict(img, by_patch_of_size=by_patch_of_size, batch_size=batch_size, padding_size=padding_size)
    end = time()
    logger.info('Elapsed time: {}s'.format(end - start))
    imageio.imwrite(destination_path, sr_img)
    return destination_path
