from app import memcache, memcache_stat
from db_access import update_db_key_list

# Update the memcache and related statistic, request access to database when a miss happened
def add_memcache(key, filename):
    if (key is not None) and (filename is not None):
        if key in memcache.keys():
            print('Key found in MemCache! Deleting the old file ', memcache[key]['filename'])
            # if the key existed in Memcache delete the old file
            os.remove(os.path.join(webapp.config['IMG_FOLDER'], memcache[key]['filename']))
            # Update memcache statistic, hit++, total request++, hit_rate++
            memcache_stat['hit'] += 1
            memcache_stat['total'] += 1
            memcache_stat['mis_rate'] = memcache_stat['mis'] / memcache_stat['total']
            memcache_stat['hit_rate'] = memcache_stat['hit'] / memcache_stat['total']
            memcache[key]['filename'] = filename
            memcache[key]['timestamp'] = datetime.now()
            update_db_key_list(key, filename)  # Update the database as well
        else:
            # if the key isn't in memcache, miss++, check Database
            update_db_key_list(key, filename)
            memcache_stat['mis'] += 1
            memcache_stat['total'] += 1
            memcache_stat['mis_rate'] = memcache_stat['mis'] / memcache_stat['total']
            memcache_stat['hit_rate'] = memcache_stat['hit'] / memcache_stat['total']
            memcache[key] = {'filename': filename, 'timestamp': datetime.now()}

    else:
        print('Error: Missing the key or file name!')
