from app import backendapp
import threading
import time
from app.memcache_access import store_stats


def store_stats_thread():
    while True:
        # store stats every 5 seconds
        store_stats()
        time.sleep(5)


if __name__ == '__main__':
    # x = threading.Thread(target=store_stats_thread())
    # x.start()
    backendapp.run(host='0.0.0.0', port=5001, debug=False)
