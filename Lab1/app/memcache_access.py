import os
from app import backendapp, memcache, memcache_stat
from db_access import update_db_key_list, get_db_filename
from datetime import datetime

def update_memcache_stat(missed):
    if missed is True:
        memcache_stat['mis'] += 1
    else:
        memcache_stat['hit'] += 1
    memcache_stat['total'] += 1
    memcache_stat['mis_rate'] = memcache_stat['mis'] / memcache_stat['total']
    memcache_stat['hit_rate'] = memcache_stat['hit'] / memcache_stat['total']


# Update the memcache and related statistic, request access to database when a miss happened
def add_memcache(key, filename):
    if (key is not None) and (filename is not None):
        if key in memcache.keys():
            print('Key found in MemCache! Deleting the old file ', memcache[key]['filename'])
            # if the key existed in Memcache delete the old file
            os.remove(os.path.join(backendapp.config['IMG_FOLDER'], memcache[key]['filename']))
            # Update memcache statistic, hit++, total request++, hit_rate++
            update_memcache_stat(missed=False)
            memcache[key]['filename'] = filename
            memcache[key]['timestamp'] = datetime.now()
            update_db_key_list(key, filename)  # Update the database as well
        else:
            # if the key isn't in memcache, miss++, check Database
            update_db_key_list(key, filename)
            update_memcache_stat(missed=True)
            memcache[key] = {'filename': filename, 'timestamp': datetime.now()}

    else:
        print('Error: Missing the key or file name!')


# Update the memcache entry
def update_memcache(key, filename):
    if (key is not None) and (filename is not None):
        memcache[key] = {'filename': filename, 'timestamp': datetime.now()}


# Get the corresponded file name with a given key in memcache
# It calls database if a memcache happened
def get_memcache(key):
    if key is not None:
        if key in memcache.keys():
            # memcache hit, update statistic
            update_memcache_stat(missed=False)
            return memcache[key]['filename']
        else:
            # memcache miss, update statistic
            update_memcache_stat(missed=True)
            # check database
            filename = get_db_filename(key)
            # add entry back to memcache
            update_memcache(key, filename)
            return filename
    else:
        return None
