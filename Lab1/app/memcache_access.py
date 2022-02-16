import os, random, sys, gc
from app import backendapp, memcache, memcache_stat, memcache_config
from app.db_access import update_db_key_list, get_db_filename, get_db
from datetime import datetime


# Return the size of a given object
def get_object_size(obj):
    marked = {id(obj)}
    obj_q = [obj]
    size = 0

    while obj_q:
        size += sum(map(sys.getsizeof, obj_q))
        all_refr = ((id(o), o) for o in gc.get_referents(*obj_q))

        # Filter object that are already marked.
        new_refr = {o_id: o for o_id, o in all_refr if o_id not in marked and not isinstance(o, type)}

        # The new obj_q will be the ones that were not marked,
        # and we will update marked with their ids so we will not traverse them again.
        obj_q = new_refr.values()
        marked.update(new_refr.keys())

    return size


# Quick estimation to the size of new entry
def get_entry_size(key, filename):
    entry = {
        'key': key,
        'filename': filename,
        'timestamp': datetime.now()
    }
    return get_object_size(entry)


# Random Replacement Policy
def random_replace_memcache(key, filename):
    # Check if memcache is empty
    if bool(memcache):
        # Randomly chose one key to drop from memcache
        thechosenone = random.choice(list(memcache.keys()))
        memcache.pop(thechosenone)
    # Add the new entry
    memcache[key] = {'filename': filename, 'timestamp': datetime.now()}
    # Update the size after replacement
    memcache_stat['size'] = get_object_size(memcache)


# LRU Replacement Policy
def lru_replace_memcache(key, filename):
    # Check if memcache is empty
    if bool(memcache):
        # Get the LRU timestamp
        oldest_timestamp = min([d['timestamp'] for d in memcache.values()])
        # Find the key by value
        for mem_key in memcache.keys():
            if memcache[mem_key]['timestamp'] == oldest_timestamp:
                print('Key', mem_key, 'found!')
                memcache.pop(mem_key)       # changed variable name b/c 'key' is confusing
    memcache[key] = {'filename': filename, 'timestamp': datetime.now()}
    # Update the size after replacement
    memcache_stat['size'] = get_object_size(memcache)


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
    memcache_stat['size'] = get_object_size(memcache)


# Update the memcache and related statistic, request access to database when a miss happened
def add_memcache(key, filename):
    if (key is not None) and (filename is not None):
        new_entry_size = get_object_size({''})
        if key in memcache.keys():
            print('Key found in MemCache! Deleting the old file ', memcache[key]['filename'])
            # If the key existed in Memcache delete the old image file
            os.remove(os.path.join(backendapp.config['IMAGE_PATH'], memcache[key]['filename']))
            # Update memcache statistic, hit++, total request++, hit_rate++
            update_memcache_stat(missed=False)
            memcache[key]['filename'] = filename
            memcache[key]['timestamp'] = datetime.now()
            update_db_key_list(key, filename)  # Update the database as well
            # Update the size after replacement
            memcache_stat['size'] = get_object_size(memcache)
        elif memcache_stat['size'] < memcache_config['capacity'] - get_entry_size(key, filename):
            # if the key isn't in memcache and memcache is not full, miss++, check Database
            update_db_key_list(key, filename)
            update_memcache_stat(missed=True)
            memcache[key] = {'filename': filename, 'timestamp': datetime.now()}
            # Update the size after replacement
            memcache_stat['size'] = get_object_size(memcache)
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


# Update the memcache entry after a miss
def update_memcache(key, filename):
    if (key is not None) and (filename is not None):
        # Check the space of memcache before update it
        if memcache_stat['size'] < memcache_config['capacity'] - get_entry_size(key, filename):
            memcache[key] = {'filename': filename, 'timestamp': datetime.now()}
            # Update the size after replacement
            memcache_stat['size'] = get_object_size(memcache)
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


# Drop all entries from the memcache
def clr_memcache():
    memcache.clear()
    # Update the size after replacement
    memcache_stat['size'] = get_object_size(memcache)
    print('memcache is cleared!')


# Delete a given key from memcache
def del_memcache(key):
    if (key is not None) and (key in memcache.keys()):
        memcache.pop(key)
        # Update the size after replacement
        memcache_stat['size'] = get_object_size(memcache)


# Called by run.py threading directly
def store_stats():
    """Function stores the state of memcache including number of items
    in cache, total size of items in cache, numbers of requests served,
    and miss/hit rate.
    :argument: None

    :return: None
    """
    # Get the number of items in cache
    nums_item = memcache_stat['nums']

    # Get the total size of images in cache
    total_size = memcache_stat['size']
    # Get the number of requests served
    nums_req = memcache_stat['total']

    # Get the miss/hit rate
    mis_rate = memcache_stat['mis']
    hit_rate = memcache_stat['hit']

    # Store stats into the database by appending row
    cnx = get_db()
    cursor = cnx.cursor()
    query = "INSERT INTO assignment_1.cache_stats (num_items, total_size, num_reqs, mis_rate, hit_rate)" \
            "VALUES (%d, %d, %d, %d, %d);"
    cursor.execute(query, (nums_item, total_size, nums_req, mis_rate, hit_rate))
    cnx.commit()
