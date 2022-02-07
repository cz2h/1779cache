import os

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    IMAGE_PATH = './image_library'
    ALLOWED_FORMAT = {'jpg', 'jpeg', 'png', 'gif', 'tiff'}
    DB_CONFIG = {
        'user': 'siyan',
        'password': 'zhangsiyan123456',
        'host': 'localhost',
        'database': 'Assignment_1'
    }
