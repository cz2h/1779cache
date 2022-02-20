import os, io
from base64 import b64encode, b64decode
from sys import getsizeof
from app import backendapp, memcache, memcache_stat, memcache_config, scheduler
from flask import render_template, url_for, request, flash, redirect, send_from_directory, json, jsonify
from app.db_access import update_db_key_list, get_db, get_db_memcache_config
from app.memcache_access import get_memcache, add_memcache, clr_memcache, del_memcache, store_stats
from werkzeug.utils import secure_filename
from config import Config


def allowed_file(filename):
    """
    # Check if uploaded file extension is acceptable
    :param filename: str
    :return: T/F
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in backendapp.config['ALLOWED_FORMAT']


# refreshConfiguration function required by frontend
@backendapp.before_first_request
def get_memcache_config():
    """ Get memcache configuration once at when the first request arrived"""
    get_db_memcache_config()
    # add the task to scheduler for memcache statistic data updates
    scheduler.add_job(id='update_memcache_state', func=store_stats, trigger='interval',
                      seconds=backendapp.config['JOB_INTERVAL'])


@backendapp.route('/', methods=['POST', 'GET'])
@backendapp.route('/index', methods=['POST'])
def main():
    """ Backend main debug page
        !!!For Debugging Only!!!
    """
    if request.method == 'POST':
        key = request.form.get('key')
        file = get_memcache(key)
        if file is not None:
            return render_template("image_viewer.html", img_data=file)

    return render_template("main.html")


# list keys from database, and display as webpage
@backendapp.route('/list_keys')
def list_keys():
    """ List all keys inside database.
        !!!For Debugging Only!!!
    """
    cnx = get_db()  # Create connection to db
    cursor = cnx.cursor()
    query = "SELECT * FROM Assignment_1.keylist"
    cursor.execute(query)
    rows = cursor.fetchall()  # Retrieve the first row that contains the key
    return render_template("list_keys.html", rows=rows)


"""
# API required for auto testing, should be in frontend
@backendapp.route('/api/list_keys', methods=['POST'])
def list_keys_api():
    cnx = get_db()  # Create connection to db
    cursor = cnx.cursor()
    query = "SELECT uniquekey FROM Assignment_1.keylist"
    cursor.execute(query)
    rows = cursor.fetchall()  # Retrieve the first row that contains the key
    result = []
    if not rows:
        return jsonify(
            success="false",
            error={
                'code': 501,
                'message': 'No file found error in list_keys_api.'}
        )
    # Flatten the list is required
    for row in rows:
        result.append(row[0])
    return jsonify(
        success='true',
        keys=result
    )
"""


@backendapp.route('/list_keys_memcache')
def list_keys_memcache():
    """ Retrieve all available keys from database
        !!!For Debugging Only!!!
    """
    return render_template("list_keys_memcache.html", memcache=memcache, memcache_stat=memcache_stat)


@backendapp.route('/put', methods=['POST'])
def put():
    """ Put function required by frontend
        add an image to memcache with a given key
        :param key: str
        :param filename: str
        :param file_size: str
    """
    key = request.form.get('key')
    file = request.form.get('value')
    response = jsonify(
        success='True'
    )
    if (key is not None) and (file is not None):
        if add_memcache(key, file) is True:
            response = jsonify(
                success='False'
            )
    return response


@backendapp.route('/get', methods=['POST'])
def get():
    """ Get function required by frontend
        Return an image stored in memcache
    """
    key = request.form.get('key')
    value = get_memcache(key)
    if value is not None:
        response = jsonify(
            content=value
        )
    else:
        response = jsonify(
            content='None'
        )

    return response


@backendapp.route('/clear', methods=['POST'])
def clear():
    """ Clear memcache function required by frontend

    """
    clr_memcache()
    response = jsonify(
        success='True'
    )
    return response


@backendapp.route('/invalidatekey', methods=['POST'])
def invalidatekey():
    """ InvalidateKey function required by frontend

    """
    key = request.form.get('key')
    response = jsonify(
        success='False'
    )
    if key is not None:
        if del_memcache(key) is True:
            response = jsonify(
                success='True'
            )

    return response


@backendapp.route('/refreshconfiguration', methods=['POST'])
def refreshconfiguration():
    """ RefreshConfiguration function required by frontend

    """
    get_db_memcache_config()
    response = jsonify(
        success='True'
    )
    return response


@backendapp.route('/upload', methods=['GET', 'POST'])
def image_upload():
    """ Upload an image with a given key to the server
        !!!For Debugging Only!!
    """
    if request.method == 'GET':
        return render_template("upload.html")

    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        print('Filename = ' + str(file))
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        # Main upload logic
        if file and allowed_file(file.filename):
            key = request.form.get('key')
            filename = secure_filename(file.filename)
            file_path = os.path.join(backendapp.config['IMAGE_PATH'], filename)
            file.save(file_path)  # write to local file system
            with open(file_path, "rb") as image_file:
                encoded_image = b64encode(image_file.read()).decode('utf-8')
            add_memcache(key, encoded_image)  # add the key and file name to cache as well as database
            return render_template("image_viewer.html", img_data=memcache[key]['file'])
    else:
        print("Method error in image_upload, wth are you doing??")


@backendapp.route('/image/<key>', methods=['GET', 'POST'])
def view_image(key):
    return render_template("image_viewer.html", img_data=memcache[key]['file'])


"""
# API required for auto testing, should be in frontend
@backendapp.route('/api/key/<key_value>', methods=['POST'])
def send_image_api(key_value):
    root_dir = os.path.dirname(os.getcwd())
    filename = get_memcache(key_value)
    try:
        with open(os.path.join(root_dir, 'Lab1', 'image_library', filename), 'rb') as binary_file:
            base64_data = base64.b64encode(binary_file.read())
            base64_msg = base64_data.decode('utf-8')
    except:
        return jsonify(
            success="false",
            error={
                "code": 501,
                "message": 'Error in retrieving '+key_value+'send_image_api'
            }
        )

    return jsonify(
        success='true',
        content=base64_msg
    )
"""
