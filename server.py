# !/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import render_template, Flask, request
import os
import time
import config
import fuck_recall
import sqlite3

# import SqliteDB

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
        status_storage_dir = status_storage_folder + username + '.pkl'

        conn = sqlite3.connect('user_info.db')
        isLoginSql = "SELECT isLogin FROM USER WHERE USERNAME = '%s'" % username
        insUserSql = "INSERT INTO USER VALUES ('%s', %d, %d)" % (username, 0, os.getpid())
        cursor = conn.execute(isLoginSql)

        count = 0
        # 如果用户名已经存在
        if (cursor.fetchone() and os.path.exists(status_storage_dir)):
            while (count < 200):
                cursor = conn.execute(isLoginSql)
                isLogin = cursor.fetchone()
                time.sleep(0.1)
                count = count + 1
                if isLogin:
                    break
            conn.close()
            if count == 200:
                return "<html>LOGIN!!!!!!!!!!!!!!!!!!</html>"
            else:
                return "<html>LOGIN SUCCESSFULLY!!!</html>"
        # 新用户
        else:
            conn.execute(insUserSql)
            conn.commit()
            conn.close()
            pid = fuck_recall.run(username)
            # 有问题！！！！！！！！！
            if pid != 0:
                while (not os.path.exists(qr_dir)):
                    time.sleep(0.1)
                return render_template('qr.html', qr_name=qr_dir)



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=config.PORT)
