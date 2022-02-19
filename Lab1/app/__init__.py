from flask import Flask
from flask_apscheduler import APScheduler
from config import Config
from datetime import datetime

global memcache  # memcache
global memcache_stat  # statistic of the memcache
global memcache_config

backendapp = Flask(__name__)

memcache = {}       # memcache = { key: {'file': b64encoded file, 'size': size(Byte),'timestamp': time_stamp} }
memcache_stat = {}
memcache_config = {}
# memcache_config =  {'capacity': 10 (MB), 'rep_policy': 'LRU'}

memcache_stat['num'] = 0        # Total num of items in cache
memcache_stat['size'] = 0       # Total size of the content in memcache
memcache_stat['total'] = 0      # Total number of requests served
memcache_stat['hit'] = 0        # Total hit count
memcache_stat['mis'] = 0        # Total missed count
memcache_stat['hit_rate'] = 0   # Overall hit rate
memcache_stat['mis_rate'] = 0   # Overall miss rate

scheduler = APScheduler()
scheduler.init_app(backendapp)
scheduler.start()

backendapp._static_folder = Config.IMAGE_PATH
backendapp.config.from_object(Config)


from app import routes

