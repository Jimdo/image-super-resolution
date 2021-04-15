import multiprocessing

bind = ":8080"
threads = multiprocessing.cpu_count() * 2 + 1
workers = multiprocessing.cpu_count() * 2 + 1
accesslogs = '/var/log/gunicorn.log'
pythonpath = '/home/ubuntu/image-super-resolution/ISR'
