import os


class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    IMAGE_PATH = './image_library'
    ALLOWED_FORMAT = {'jpg', 'jpeg', 'png', 'gif', 'tiff'}

    DB_CONFIG = {
        'user': 'root',
        'password': 'Actonwang29',
        'host': 'localhost',
        'database': 'assignment_1'
    }
