from flask import Flask
from config import Config

# global memcache  # memcache
# global memcache_stat  # statistic of the memcache

backendapp = Flask(__name__)
memcache = {}
memcache_stat = {}
memcache_stat['hit'] = 0
memcache_stat['mis'] = 0
memcache_stat['total'] = 0

backendapp._static_folder = Config.IMAGE_PATH
backendapp.config.from_object(Config)

from app import routes

