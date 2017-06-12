# !/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import render_template, Flask, request
import os
import time
import config
import fuck_recall
app = Flask(__name__)


qr_folder = config.qr_folder

# 可以在线扫描二维码
# @app.route('/qr')
# def get_QR():
#     return render_template('qr.html')

# 简单的加密验证，防止任何人都能看到缓存的图片
# @app.route('/<auth_code>/<filename>/')
# def get_pic(auth_code=None, filename=None):
#     m = hashlib.md5()
#     m.update(filename + config.SALT)
#     md5_code = m.hexdigest()
#     if auth_code == md5_code:
#         return render_template('chat_file.html', file_name=filename)

@app.route('/fuck_recall_login.html', methods=['GET', 'POST'])
def fuck_recall_login():
    if request.method == 'GET':
        return render_template('signin.html')
    elif request.method == 'POST':
        username = request.form['username']
        qr_dir = qr_folder + username + '.jpg'
        fuck_recall.run(username)
        while(not os.path.exists(qr_dir)):
            time.sleep(0.1)
        return render_template('qr.html', qr_name=qr_dir)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=config.PORT)
