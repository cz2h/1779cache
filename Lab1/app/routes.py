from app import backendapp, memcache, memcache_stat
from flask import render_template


@backendapp.route('/')
@backendapp.route('/index')
def index():
    user = {
        'username': 'John',
        'login': True
    }
    return render_template('index.html', title='Home', user=user)
