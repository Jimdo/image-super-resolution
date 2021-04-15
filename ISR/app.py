import os
from importlib import import_module
from pathlib import Path
from time import time

import imageio
from flask import Flask, request, send_from_directory
import yaml

from ISR.utils.logger import get_logger
from ISR.utils.utils import get_timestamp, get_config_from_weights

import tensorflow as tf
print("Num GPUs Available: ", len(tf.config.list_physical_devices('GPU')))

def _get_module(generator):
    return import_module('ISR.models.' + generator)


def _setup_model(model):
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


def run(url, gen, patch_size):
    output_dir = Path('./data/output') / get_timestamp()
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / (url[-15:] + '.jpg')
    logger = get_logger(__name__)
    logger.info('Downloading file\n > {}'.format(url))
    img = imageio.imread(url)
    logger.info('Result will be saved in\n > {}'.format(output_path))
    start = time()
    sr_img = gen.predict(img, by_patch_of_size=patch_size)
    end = time()
    logger.info('Elapsed time: {}s'.format(end - start))
    imageio.imwrite(output_path, sr_img)
    return output_path


app = Flask(__name__)


@app.route('/magnify')
def magnify():
    # Available Models
    # RDN: psnr-large, psnr-small, noise-cancel
    # RRDN: gans
    model = request.args.get('model') or 'noise-cancel'
    logger = get_logger(__name__)
    logger.info('Magnifying with {}'.format(model))
    gen = _setup_model(model)
    url = request.args.get('image_url')
    patch_size = request.args.get('patch_size')
    filepath = run(url, gen, patch_size)
    directory = str(filepath.parent.absolute())
    filename = str(filepath.name)
    return send_from_directory(directory, filename, as_attachment=True, attachment_filename='sharpened.jpg')


@app.route('/')
@app.route('/health')
def health_check():
    logger = get_logger(__name__)
    logger.info('Health Check: OK')
    return 'OK'
