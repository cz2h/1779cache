import mysql.connector
from mysql.connector import errorcode
from flask import g
from app import backendapp


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
    else:
        cnx.close()


# Create g object for Flask to handle the SQL access
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = connect_to_database()
    return db

# update the database based on the given key and filename
def update_db_key_list(key, filename):
    cnx = get_db()  # Create connection to db
    cursor = cnx.cursor()
    query = "SELECT uniquekey FROM Assignment_1.key_list WHERE uniquekey = %s;"
    cursor.execute(query, (key,))
    row = cursor.fetchone()  # Retrieve the first row that contains the key
    # Check if database has the key
    if row is None:  # Key is not in database, add new entry
        query = "INSERT INTO Assignment_1.key_list (uniquekey, filename) VALUE ( %s, %s);"
        cursor.execute(query, (key, filename))
        cnx.commit()
        print('Fresh key found! Adding new file ', filename, 'to DB')
    else:  # The given key is in database, update existing item
        query = "UPDATE Assignment_1.key_list SET filename = %s WHERE uniquekey = %s;"
        cursor.execute(query, (filename, key))
        cnx.commit()
        print('Key found in DB! Updating new file name ', filename)

# get the corresponded file name of a given key from database
def get_db_filename(key):
    cnx = get_db()  # Create connection to db
    cursor = cnx.cursor()
    query = "SELECT filename FROM Assignment_1.key_list WHERE uniquekey = %s;"
    cursor.execute(query, (key,))
    row = cursor.fetchone()  # Retrieve the first row that contains the key
    # Check if database has the key
    if row is None:  # Key is not in database, add new entry
        print('No key found in DB!')
    else:  # The given key is in database, update existing item
        return row[0]
