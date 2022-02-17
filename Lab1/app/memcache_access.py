import os, random, sys, gc
from app import backendapp, memcache, memcache_stat, memcache_config
from app.db_access import update_db_key_list, get_db_filename, get_db, get_db_filesize
from datetime import datetime


# Random Replacement Policy
def random_replace_memcache():
    # Check if memcache is empty
    if bool(memcache):
        # Randomly chose one key to drop from memcache
        rand_key = random.choice(list(memcache.keys()))
        memcache.pop(rand_key)
        memcache_stat['size'] -= get_db_filesize(rand_key)
    else:
        print("Error in replacement, can't pop anymore because memcache is already empty. ")


# LRU Replacement Policy
def lru_replace_memcache():
    # Check if memcache is empty
    if bool(memcache):
        # Get the LRU timestamp
        oldest_timestamp = min([d['timestamp'] for d in memcache.values()])
        # Find the key by value
        for mem_key in memcache.keys():
            if memcache[mem_key]['timestamp'] == oldest_timestamp:
                memcache_stat['size'] -= get_db_filesize(mem_key)
                memcache.pop(mem_key)
                return
    else:
        print("Error in replacement, can't pop anymore because memcache is already empty. ")


def replace_memcache():
    """Execute a replacement policy specified by memcache_config['rep_policy']
        This function will only pop from

    :param key: str
    :param filename: str
    :return: None
    """
    if memcache_config['rep_policy'] == 'RANDOM':
        random_replace_memcache()
    elif memcache_config['rep_policy'] == 'LRU':
        lru_replace_memcache()

    memcache_stat['num'] -= 1


# Update the memcache statistic data
def update_memcache_stat(missed):
    """Keep in mind this function does NOT update 'num' or 'size' of memcache
        which makes it usable for missed situations

    :param missed: Bool
    :return: None
    """
    if missed:
        memcache_stat['mis'] += 1
    else:
        memcache_stat['hit'] += 1
    memcache_stat['total'] += 1
    memcache_stat['mis_rate'] = memcache_stat['mis'] / memcache_stat['total']
    memcache_stat['hit_rate'] = memcache_stat['hit'] / memcache_stat['total']


def add_memcache(key, filename, image_size):
    """Update the memcache and related statistic, request access to database when a miss happened

    :param key: str
    :param filename: str
    :param image_size: float
    :return: None
    """
    # If the key existed in Memcache, we need to update the size by subtracting by the old file size
    if key in memcache.keys():
        old_file_size = get_db_filesize(key)
        if old_file_size is None:   # memcache & DB inconsistency, found in memcache but not in DB
            print("Returning in add_memcache, old file not found. Key in memcache = %d")
            return

        # Update memcache statistic('num' in cache is not changing yet b/c we don't need to pop that entry)
        memcache_stat['size'] -= old_file_size

    # Store the file into memcache(replace other cache files if needed)
    # Keep popping until we have enough space in memcache for the new image
    while memcache_stat['size'] + image_size > memcache_config['capacity']:
        replace_memcache()   # stats are updated inside
    if key in memcache.keys():
        memcache[key]['filename'] = filename  # update/add it to memcache
        memcache[key]['timestamp'] = datetime.now()
    else:
        memcache[key] = {
            'filename': filename,
            'timestamp': datetime.now()
        }
    # Insert file info to the database(auto-replace previous entry in DB)
    update_db_key_list(key, filename, image_size)
    # Update the size after replacement(not updating 'num' b/c we are just replacing)
    memcache_stat['size'] += image_size


# Get the corresponded file name with a given key in memcache
# It calls database if a memcache miss happened
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
        if filename is not None:
            update_memcache(key, filename)
        else:
            print('Key is not found!')
        return filename



# Update the memcache entry retrieved from database after a miss
def update_memcache(key, filename):
    f_size = get_db_filesize(key)
    while memcache_stat['size'] + f_size > memcache_config['capacity']:
        # keep removing entries from memcache until the item can fit into memcache
        replace_memcache()

    memcache[key] = {
        'filename': filename,
        'timestamp': datetime.now()
    }
    memcache_stat['num'] += 1
    memcache_stat['size'] += f_size


# Drop all entries from the memcache
def clr_memcache():
    memcache.clear()
    memcache_stat['size'] = 0
    print('memcache is cleared!')


# Delete a given key from memcache
def del_memcache(key):
    if (key is not None) and (key in memcache.keys()):
        memcache.pop(key)
        memcache_stat['size'] -= get_db_filesize(key)
    else:
        print('Error in del_memcache, Key not found in memcache.')


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
