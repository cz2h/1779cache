import os, random, sys, gc
from app import backendapp, memcache, memcache_stat, memcache_config
from app.db_access import update_db_key_list, get_db_filename
from datetime import datetime


def get_memcache_size(obj):
    marked = {id(obj)}
    obj_q = [obj]
    sz = 0

    while obj_q:
        sz += sum(map(sys.getsizeof, obj_q))
        all_refr = ((id(o), o) for o in gc.get_referents(*obj_q))

        # Filter object that are already marked.
        new_refr = {o_id: o for o_id, o in all_refr if o_id not in marked and not isinstance(o, type)}

        # The new obj_q will be the ones that were not marked,
        # and we will update marked with their ids so we will not traverse them again.
        obj_q = new_refr.values()
        marked.update(new_refr.keys())

    return sz


# Random Replacment Policy
def random_replace_memcache(key, filename):
    # Randomly chose one key to drop from memcache
    thechosenone = random.choice(list(memcache.keys()))
    memcache.pop(thechosenone)
    # Add the new entry
    memcache[key] = {'filename': filename, 'timestamp': datetime.now()}


# LRU Replacement Policy
def lru_replace_memcache(key, filename):
    # Get the LRU timestamp
    oldest_timestamp = min([d['timestamp'] for d in memcache.values()])
    # Find the key by value
    for key in memcache.keys():
        if(memcache[key]['timestamp'] == oldest_timestamp):
            print('Key', key, 'found!')
            memcache.pop(key)
    memcache[key] = {'filename': filename, 'timestamp': datetime.now()}


# Update the memcache statistic data
def update_memcache_stat(missed):
    if missed is True:
        memcache_stat['mis'] += 1
    else:
        memcache_stat['hit'] += 1
    memcache_stat['total'] += 1
    memcache_stat['mis_rate'] = memcache_stat['mis'] / memcache_stat['total']
    memcache_stat['hit_rate'] = memcache_stat['hit'] / memcache_stat['total']
    # Calculate the current memcache size
    memcache_stat['size'] = get_memcache_size(memcache)


# Update the memcache and related statistic, request access to database when a miss happened
def add_memcache(key, filename):
    if (key is not None) and (filename is not None):
        if key in memcache.keys():
            print('Key found in MemCache! Deleting the old file ', memcache[key]['filename'])
            # If the key existed in Memcache delete the old image file
            os.remove(os.path.join(backendapp.config['IMAGE_PATH'], memcache[key]['filename']))
            # Update memcache statistic, hit++, total request++, hit_rate++
            update_memcache_stat(missed=False)
            memcache[key]['filename'] = filename
            memcache[key]['timestamp'] = datetime.now()
            update_db_key_list(key, filename)  # Update the database as well
        elif memcache_stat['size'] < memcache_config['capacity']:
            # if the key isn't in memcache and memcache is not full, miss++, check Database
            update_db_key_list(key, filename)
            update_memcache_stat(missed=True)
            memcache[key] = {'filename': filename, 'timestamp': datetime.now()}
        else:
            # if the key isn't in memcache and memcache is full call the replacement routine
            print('MemCache is Full! Call for replacement routine!')
            if memcache_config['rep_policy'] == 'RANDOM':
                random_replace_memcache(key, filename)
            elif memcache_config['rep_policy'] == 'LRU':
                lru_replace_memcache(key, filename)
            update_memcache_stat(missed=True)
    else:
        print('Error add_memcache: Missing the key or file name!')


# Update the memcache entry
def update_memcache(key, filename):
    if (key is not None) and (filename is not None):
        # Check the space of memcache before update it
        if memcache_stat['size'] < memcache_config['capacity']:
            memcache[key] = {'filename': filename, 'timestamp': datetime.now()}
        else:
            print('MemCache is Full! Call for replacement routine!')
            if memcache_config['rep_policy'] == 'RANDOM':
                random_replace_memcache(key, filename)
            elif memcache_config['rep_policy'] == 'LRU':
                lru_replace_memcache(key, filename)


# Get the corresponded file name with a given key in memcache
# It calls database if a memcache happened
def get_memcache(key):
    if key is None:
        return None

    if key in memcache.keys():
        # memcache hit, update statistic and request time
        update_memcache_stat(missed=False)
        memcache[key]['timestamp'] = datetime.now()
        return memcache[key]['filename']
    else:
        # memcache miss, update statistic
        update_memcache_stat(missed=True)
        # check database
        filename = get_db_filename(key)
        # add entry back to memcache
        update_memcache(key, filename)
        return filename

