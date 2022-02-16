from flask import Flask
from config import Config

global memcache  # memcache
global memcache_stat  # statistic of the memcache
global memcache_config

backendapp = Flask(__name__)

memcache = {}       # memcache = { key: {'filename': f_name, 'timestamp': time_stamp} }
memcache_stat = {}
memcache_config = {}
# memcache_config =  {'capacity': 10 (MB), 'rep_policy': 'LRU'}

memcache_stat['num'] = 0        # total num of items in cache
memcache_stat['hit'] = 0
memcache_stat['mis'] = 0
memcache_stat['total'] = 0      # total number of requests served
memcache_stat['size'] = 0

backendapp._static_folder = Config.IMAGE_PATH
backendapp.config.from_object(Config)

from app import routes

