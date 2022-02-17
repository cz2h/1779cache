import os


class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    IMAGE_PATH = './image_library'
    ALLOWED_FORMAT = {'jpg', 'jpeg', 'png', 'gif', 'tiff'}
    SCHEDULER_API_ENABLED = True
    SCHEDULER_TIMEZONE = "America/Toronto"
    DB_CONFIG = {
        'user': 'siyan',
        'password': 'zhangsiyan123456',
        'host': 'localhost',
        'database': 'Assignment_1'
    }



