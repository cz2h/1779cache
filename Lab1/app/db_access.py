import mysql.connector
from mysql.connector import errorcode
from flask import g
from app import backendapp, memcache_config


# initiate connection to database
def connect_to_database():
    try:
        return mysql.connector.connect(user=backendapp.config['DB_CONFIG']['user'],
                                       password=backendapp.config['DB_CONFIG']['password'],
                                       host=backendapp.config['DB_CONFIG']['host'],
                                       database=backendapp.config['DB_CONFIG']['database'])
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print(err)


#    else:
#        cnx.close()


# Create g object for Flask to handle the SQL access
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = connect_to_database()
    return db


def update_db_key_list(key, filename, image_size):
    """
    Add key, filename to database if not in DB, update existing row if key is there already
    !!!For Debugging Only!!!
    :param key: str
    :param filename: str
    :param image_size: float
    :return:
    """
    cnx = get_db()  # Create connection to db
    cursor = cnx.cursor()
    query = "SELECT uniquekey FROM Assignment_1.keylist WHERE uniquekey = %s;"
    cursor.execute(query, (key,))
    row = cursor.fetchone()  # Retrieve the first row that contains the key
    # Check if database has the key
    if row is None:  # Key is not in database, add new entry
        query = "INSERT INTO Assignment_1.keylist (uniquekey, filename, image_size) VALUE ( %s, %s, %s);"
        cursor.execute(query, (key, filename, image_size))
        cnx.commit()
        print('Fresh key found! Adding new file ', filename, 'to DB')
    else:  # The given key is in database, update existing item
        query = "UPDATE Assignment_1.keylist SET filename = %s, image_size = %s WHERE uniquekey = %s;"
        cursor.execute(query, (filename, image_size, key))
        cnx.commit()
        print('Key found in DB! Updating new file name ', filename)



def get_db_filename(key):
    """
    get the corresponded file name of a given key from database
    !!!For Debugging Only!!!
    :param key: str
    :return: filename: str
    """
    cnx = get_db()  # Create connection to db
    cursor = cnx.cursor()
    query = "SELECT filename FROM Assignment_1.keylist WHERE uniquekey = %s;"
    cursor.execute(query, (key,))
    row = cursor.fetchone()  # Retrieve the first row that contains the key
    # Check if database has the key
    if row is None:  # Key is not in database, add new entry
        print('Key not found in Memcache or DB!')
        return None
    else:  # The given key is in database, update existing item
        return row[0]


def get_db_filesize(key):
    """ Get the corresponding file size of an image given key from the database
    !!!For Debugging Only!!!
    :param key: the given key of the desired image size: str
    :return: image file size: float
    """
    cursor = get_db().cursor()
    query = "SELECT image_size FROM Assignment_1.keylist WHERE uniquekey = %s;"
    cursor.execute(query, (key,))
    row = cursor.fetchone()
    if row is None:
        print("No key found in DB while searching image size with key in get_db_filesize, "
              "adding memcache_failed and returned")
        return None
    return row[0]   # return the image size


def get_db_memcache_config():
    """
    retrieve the memcaceh configuration from database

    :return:
    """
    cnx = get_db()  # Create connection to db
    cursor = cnx.cursor()
    query = "SELECT * FROM Assignment_1.memcache_config"
    cursor.execute(query)
    row = cursor.fetchone()  # Retrieve the first row that contains the configuration
    if row is not None:
        memcache_config['capacity'] = row[0]
        memcache_config['rep_policy'] = row[1]
        print('Configuration is found in database, capacity:', row[0], 'MB,', row[1])
    else:  # default
        memcache_config['capacity'] = 10
        memcache_config['rep_policy'] = 'RANDOM'
        print('No configuration is not found in database, switch to default configuration')
