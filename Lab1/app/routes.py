import os, base64
from app import backendapp, memcache, memcache_stat, memcache_config, scheduler
from flask import render_template, url_for, request, flash, redirect, send_from_directory, json, jsonify
from app.db_access import update_db_key_list, get_db, get_db_memcache_config
from app.memcache_access import get_memcache, add_memcache, clr_memcache, del_memcache, store_stats
from werkzeug.utils import secure_filename
from config import Config


# Check if uploaded file extension is acceptable
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in backendapp.config['ALLOWED_FORMAT']


# refreshConfiguration function required by frontend
@backendapp.before_first_request
def get_memcache_config():
    """ Get memcache configuration once at when the first request arrived"""
    get_db_memcache_config()
    # add the task to scheduler for memcache statistic data updates
    scheduler.add_job(id='update_memcache_state', func=store_stats, trigger='interval', seconds=10)


@backendapp.route('/', methods=['POST', 'GET'])
@backendapp.route('/index', methods=['POST'])
def main():
    """ Backend main debug page
        !!!For Debugging Only!!!
    """
    if request.method == 'POST':
        key = request.form.get('key')
        filename = get_memcache(key)
        if filename is not None:
            return redirect(url_for('download_file', name=filename))
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
        :param key: str
        :param filename: str
        :param file_size: str
    """
    key = request.form.get('key')
    filename = request.form.get('value')
    image_size = request.form.get('file_size')
    if (key is not None) and (filename is not None) and (image_size is not None):
        add_memcache(key, filename, float(image_size))
        response = backendapp.response_class(
            response=json.dumps("OK"),
            status=200,
            mimetype='application/json'
        )
    else:
        response = backendapp.response_class(
            response=json.dumps("Bad Request"),
            status=400,
            mimetype='application/json'
        )

    return response


@backendapp.route('/get', methods=['POST'])
def get():
    """ Get function required by frontend

    """
    key = request.form.get('key')
    value = get_memcache(key)
    if value is not None:
        response = backendapp.response_class(
            response=json.dumps(value),
            status=200,
            mimetype='application/json'
        )
    else:
        response = backendapp.response_class(
            response=json.dumps("Unknown key"),
            status=400,
            mimetype='application/json'
        )

    return response


@backendapp.route('/clear', methods=['POST'])
def clear():
    """ Clear memcache function required by frontend

    """
    clr_memcache()
    response = backendapp.response_class(
        response=json.dumps("OK"),
        status=200,
        mimetype='application/json'
    )

    return response


@backendapp.route('/invalidatekey', methods=['POST'])
def invalidatekey():
    """ InvalidateKey function required by frontend

    """
    key = request.form.get('key')
    if key is not None:
        del_memcache(key)
        response = backendapp.response_class(
            response=json.dumps("OK"),
            status=200,
            mimetype='application/json'
        )
    else:
        response = backendapp.response_class(
            response=json.dumps("Unknown key"),
            status=400,
            mimetype='application/json'
        )

    return response


@backendapp.route('/refreshconfiguration', methods=['POST'])
def refreshconfiguration():
    """ RefreshConfiguration function required by frontend

    """
    get_db_memcache_config()
    response = backendapp.response_class(
        response=json.dumps("OK"),
        status=200,
        mimetype='application/json'
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
            image_size = float(request.args.get('file_size'))
            file.save(os.path.join(backendapp.config['IMAGE_PATH'], filename))  # write to local file system
            add_memcache(key, filename, image_size)  # add the key and file name to cache as well as database
            return redirect(url_for('download_file', name=filename))
    else:
        print("Method error in image_upload, wth are you doing??")


@backendapp.route('/uploaded/<name>', methods=['GET', 'POST'])
def download_file(name):
    """ display an image for a given file name
        !!!For Debugging Only!!
    """
    root_dir = os.path.dirname(os.getcwd())
    print(name)
    return send_from_directory(os.path.join(root_dir, 'Lab1', 'image_library'), name)


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
