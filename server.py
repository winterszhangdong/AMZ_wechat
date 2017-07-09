# !/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import render_template, Flask, request
import os
import time
import config
import fuck_recall
import sqlite3

app = Flask(__name__)

qr_folder = config.qr_folder
status_storage_folder = config.status_storage_folder
fuck_recall.pid_logger(os.getpid(), 'a')


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
        status_dir = status_storage_folder + username + '.pkl'

        isLoginSql = "SELECT isLogin FROM USER WHERE USERNAME = '%s'" % username
        conn = sqlite3.connect('user_info.db')

        pid = fuck_recall.run(username)
        if pid == 0:
            os._exit(0)

        if (os.path.exists(status_dir)):
            for i in xrange(200):
                qrExists = os.path.exists(qr_dir)
                isLogin = conn.execute(isLoginSql).fetchone()[0]
                if qrExists:
                    html = render_template('qr.html', qr_name=qr_dir)
                    break
                elif isLogin:
                    html =  "<html>LOGIN SUCCESSFULLY!!!</html>"
                    break
                else:
                    time.sleep(0.1)
            else:
                html = "<html>LOGIN PLEASE!!!!!!!!!!!!!!!!</html>"

        else:
            while (not os.path.exists(qr_dir)):
                time.sleep(0.1)
            html = render_template('qr.html', qr_name=qr_dir)

        conn.close()
        return html

def startWebserver():
    app.run(host='0.0.0.0', port=config.PORT, use_reloader=False)

if __name__ == '__main__':
    startWebserver()
    # app.run(host='0.0.0.0', port=config.PORT, processes=2)
