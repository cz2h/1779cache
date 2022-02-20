# 1779frontend
Front end flask server code

# Project structure

### React repo
This app will serve the html pages to user. This app only communicates with 'Front end flask'.
https://github.com/zengchu2/frontend

### Front end flask
This app can upload, get images and save (file_key, file_name) pair to db.
Also this app will communicate with 'Memcache flask' to get cached file content and ask memcache to update its configuartion.
https://github.com/zengchu2/1779frontend/

### Memcache flask 
This is a memcache instance storing (key, name) pair, have different evict policy.
https://github.com/actwang/ECE1779
