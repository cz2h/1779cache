import random
from sys import getsizeof
from app import backendapp, memcache, memcache_stat, memcache_config
from app.db_access import update_db_key_list, get_db_filename, get_db, get_db_filesize, connect_to_database
from datetime import datetime


# Random Replacement Policy
def random_replace_memcache():
    # Check if memcache is empty
    if bool(memcache):
        # Randomly chose one key to drop from memcache
        rand_key = random.choice(list(memcache.keys()))
        memcache_stat['size'] -= memcache[rand_key]['size']
        memcache.pop(rand_key)
        return True
    else:
        print("Error in replacement, can't pop anymore because memcache is already empty. ")
        return False


# LRU Replacement Policy
def lru_replace_memcache():
    # Check if memcache is empty
    if bool(memcache):
        # Get the LRU timestamp
        oldest_timestamp = min([d['timestamp'] for d in memcache.values()])
        # Find the key by value
        for mem_key in memcache.keys():
            if memcache[mem_key]['timestamp'] == oldest_timestamp:
                memcache_stat['size'] -= memcache[mem_key]['size']
                memcache.pop(mem_key)
                return True
    else:
        print("Error in replacement, can't pop anymore because memcache is already empty. ")
        return False


def replace_memcache():
    """Execute a replacement policy specified by memcache_config['rep_policy']
        This function will only pop from memcache, not the actual replacement.
        New entry will be added by whoever called this function.
    """
    succeed = False
    if memcache_config['rep_policy'] == 'RANDOM':
        succeed = random_replace_memcache()
    elif memcache_config['rep_policy'] == 'LRU':
        succeed = lru_replace_memcache()
    # make sure no error happened during pop
    if succeed is True:
        memcache_stat['num'] -= 1


def update_memcache_stat(missed):
    """Keep in mind this function does NOT update 'num' or 'size' of memcache
        which makes it usable for missed situations

    :param missed: bool
    :return: None
    """
    if missed:
        memcache_stat['mis'] += 1
    else:
        memcache_stat['hit'] += 1
    memcache_stat['total'] += 1
    memcache_stat['mis_rate'] = memcache_stat['mis'] / memcache_stat['total']
    memcache_stat['hit_rate'] = memcache_stat['hit'] / memcache_stat['total']


def add_memcache(key, file):
    """Update the memcache and related statistic, request access to database when a miss happened

    :param key: str
    :param file: str
    :return: None
    """
    # converts the image size to MB. There is 49 Bytes of overhead in string object
    image_size = (getsizeof(file) - 49) / 1024 / 1024
    # check if image can be fit into the memcache before everything else
    if image_size > memcache_config['capacity']:
        print('The given file is exceeded the capacity of the memcache')
        return False

    # If the key existed in Memcache, we need to update the size by subtracting by the old file size
    if key in memcache.keys():
        old_file_size = memcache[key]['size']
        if old_file_size is None:   # memcache & DB inconsistency, found in memcache but not in DB
            print("Returning in add_memcache, old file not found. Key in memcache = %d")
            return False
        # Update memcache statistic('num' in cache is not changing yet b/c we don't need to pop that entry)
        memcache_stat['size'] -= old_file_size

    # Store the file into memcache(replace other cache files if needed)
    # Keep popping until we have enough space in memcache for the new image
    while memcache_stat['size'] + image_size > memcache_config['capacity']:
        replace_memcache()   # stats are updated inside

    if key in memcache.keys():
        memcache[key]['file'] = file            # update/add it to memcache
        memcache[key]['size'] = image_size      # update the new file size
        memcache[key]['timestamp'] = datetime.now()
    else:
        # add new entry if kay doesn't exist
        memcache_stat['num'] += 1
        memcache[key] = {
            'file': file,
            'size': image_size,
            'timestamp': datetime.now()
        }
    # Insert file info to the database(auto-replace previous entry in DB)
    # update_db_key_list(key, filename, image_size)
    # Update the size after replacement(not updating 'num' b/c we are just replacing)
    memcache_stat['size'] += image_size
    return True


def get_memcache(key):
    """
    Get the corresponded file content in base64 with a given key in memcache

    :param key: str
    :return: file: str
    """
    if key is None:
        return None

    if key in memcache.keys():
        # memcache hit, update statistic and request time
        update_memcache_stat(missed=False)
        memcache[key]['timestamp'] = datetime.now()
        return memcache[key]['file']
    else:
        # memcache miss, update statistic
        update_memcache_stat(missed=True)
        return None


"""
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
"""


# Drop all entries from the memcache
def clr_memcache():
    memcache.clear()
    memcache_stat['size'] = 0
    print('memcache is cleared!')


# Delete a given key from memcache
def del_memcache(key):
    if (key is not None) and (key in memcache.keys()):
        memcache_stat['size'] -= memcache[key]['size']
        memcache.pop(key)
        return True
    else:
        print('Error in del_memcache, Key not found in memcache.')
        return False


# Called by run.py threading directly
def store_stats():
    """Function stores the state of memcache including number of items
    in cache, total size of items in cache, numbers of requests served,
    and miss/hit rate.
    :argument: None

    :return: None
    """
    print('Start update memcache status!')
    current_time = datetime.now()
    # Get the number of items in cache
    num_items = memcache_stat['num']

    # Get the total size of images in cache
    total_size = memcache_stat['size']
    # Get the number of requests served
    num_reqs = memcache_stat['total']

    # Get the miss/hit rate
    mis_rate = memcache_stat['mis_rate']
    hit_rate = memcache_stat['hit_rate']

    # Store stats into the database by appending row
    cnx = connect_to_database()
    cursor = cnx.cursor()
    query = "INSERT INTO Assignment_1.cache_stats (num_items, total_size, num_reqs, mis_rate, hit_rate, time_stamp)" \
            "VALUES (%s, %s, %s, %s, %s, %s);"
    cursor.execute(query, (num_items, total_size, num_reqs, mis_rate, hit_rate, current_time))
    cnx.commit()
    print('Status Saved! Timestamp is: ', current_time)
