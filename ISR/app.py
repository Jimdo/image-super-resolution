import os
from importlib import import_module
from pathlib import Path
from time import time
from multiprocessing import Process
import imageio
from flask import Flask, request, send_from_directory, abort
import yaml
import string
from ISR.utils.logger import get_logger
from ISR.utils.utils import get_timestamp, get_config_from_weights
import random
from urllib.parse import unquote


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


def predict(url, model_name, destination_path):
    physical_devices = []
    if is_gpu():
        import tensorflow as tf
        physical_devices = tf.config.list_physical_devices('GPU')
        tf.config.experimental.set_memory_growth(physical_devices[0], True)

    logger.info("Num GPUs Available: {}".format(len(physical_devices)))
    logger.info('Magnifying with {}'.format(model_name))
    gen = _setup_model(model_name)
    run(url, gen, destination_path)


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


def run(url, gen, destination_path):
    logger = get_logger(__name__)
    logger.info('Downloading file\n > {}'.format(url))
    img = imageio.imread(url)
    logger.info('Result will be saved in\n > {}'.format(destination_path))
    start = time()
    sr_img = gen.predict(img)
    end = time()
    logger.info('Elapsed time: {}s'.format(end - start))
    imageio.imwrite(destination_path, sr_img)
    return destination_path


app = Flask(__name__)
logger = get_logger(__name__)
logger.info('Started in ' + ('GPU' if is_gpu() else 'CPU') + ' mode')


@app.route('/magnify')
def magnify():
    logger = get_logger(__name__)
    url = unquote(request.args.get('image_url'))
    if check_origin(url) is False:
        logger.info('processing denied: ' + url)
        return abort(403)

    model_name = request.args.get('model') or 'noise-cancel'
    filepath = destination()
    logger.info('starting prediction in ' + ('GPU' if is_gpu() else 'CPU') + ' mode')
    p = Process(target=predict, args=(url, model_name, filepath))
    p.start()
    p.join()
    directory = str(filepath.parent.absolute())
    filename = str(filepath.name)
    logger.info('sending prediction')

    return send_from_directory(directory, filename, as_attachment=True, attachment_filename='sharpened.jpg')


@app.route('/')
@app.route('/health')
def health_check():
    return 'OK'
