import os, base64
from app import backendapp, memcache, memcache_stat
from flask import render_template, url_for, request, flash, redirect, send_from_directory, json, jsonify
from db_access import update_db_key_list, get_db
from memcache_access import get_memcache
from werkzeug.utils import secure_filename
from memcache_access import add_memcache


# Check if uploaded file extension is acceptable
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in backendapp.config['ALLOWED_FORMAT']


@backendapp.route('/', methods=['POST', 'GET'])
@backendapp.route('/index', methods=['POST'])
def main():
    if request.method == 'POST':
        key = request.form.get('key')
        filename = get_memcache(key)
        return redirect(url_for('download_file', name=filename))
    return render_template("main.html")


# list keys from database, and display as webpage
@backendapp.route('/list_keys')
def list_keys():
    cnx = get_db()  # Create connection to db
    cursor = cnx.cursor()
    query = "SELECT * FROM Assignment_1.key_list"
    cursor.execute(query)
    rows = cursor.fetchall()  # Retrieve the first row that contains the key
    return render_template("list_keys.html", rows=rows)


@backendapp.route('/api/list_keys', methods=['POST'])
def list_keys_api():
    cnx = get_db()  # Create connection to db
    cursor = cnx.cursor()
    query = "SELECT uniquekey FROM Assignment_1.key_list"
    cursor.execute(query)
    rows = cursor.fetchall()  # Retrieve the first row that contains the key
    result = []
    # Flatten the list is required
    for row in rows:
        result.append(row[0])
    return jsonify(
        success='true',
        keys=result
    )


@backendapp.route('/list_keys_memcache')
def list_keys_memcache():
    # Retrieve all available keys from database
    return render_template("list_keys_memcache.html", memcache=memcache, memcache_stat=memcache_stat)


@backendapp.route('/upload', methods=['GET', 'POST'])
def image_upload():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            key = request.form.get('key')
            filename = secure_filename(file.filename)
            add_memcache(key, filename)  # add the key and file name to cache as well as database
            file.save(os.path.join(backendapp.config['IMG_FOLDER'], filename))
            return redirect(url_for('download_file', name=filename))
    return render_template("upload.html")


@backendapp.route('/uploaded/<name>', methods=['GET', 'POST'])
def download_file(name):
    if request.method == 'GET':
        root_dir = os.path.dirname(os.getcwd())
        print(name)
        return send_from_directory(os.path.join(root_dir, 'MemCacheExample', 'image_library'), name)

@backendapp.route('/api/key/<key_value>', methods=['POST'])
def send_image_api():
    key = request.form.get('key_value')
    root_dir = os.path.dirname(os.getcwd())
    filename = get_memcache(key)
    with open(os.path.join(root_dir, 'MemCacheExample', 'image_library', filename), 'rb') as binary_file:
        binary_data = binary_file.read()
        base64_data = base64.b64encode(binary_data)
        base64_msg = base64_data.decode('utf-8')

    return jsonify(
        success='true',
        content=base64_msg
    )
