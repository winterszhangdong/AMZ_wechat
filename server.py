# !/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

reload(sys)
sys.setdefaultencoding('utf-8')

from flask import render_template, Flask, request
import os
import time
import config
import fuck_recall

app = Flask(__name__)

qr_folder = config.qr_folder
status_storage_folder = config.status_storage_folder
fuck_recall.pid_logger(os.getpid(), 'a')


@app.route('/wechat.html', methods=['GET', 'POST'])
def fuck_recall_login():
    if request.method == 'GET':
        return render_template('signin.html')
    elif request.method == 'POST':
        username = request.form['username']
        qr_dir = qr_folder + username + '.jpg'
        status_dir = status_storage_folder + username + '.pkl'

        pid = fuck_recall.run(username)
        if pid == 0:
            os._exit(0)

        if os.path.exists(status_dir):
            for i in xrange(200):
                qrExists = os.path.exists(qr_dir)
                if qrExists:
                    html = render_template('qr.html', qr_name=qr_dir)
                    break
                elif fuck_recall.is_login():
                    html = "<html>LOGIN SUCCESSFULLY!!!</html>"
                    break
                else:
                    time.sleep(0.1)
            else:
                html = "<html>LOGIN PLEASE!!!!!!!!!!!!!!!!</html>"

        else:
            while not os.path.exists(qr_dir):
                time.sleep(0.1)
            html = render_template('qr.html', qr_name=qr_dir)

        return html


def _start_webserver():
    app.run(host='0.0.0.0', port=config.PORT)


def _new_pid_file():
    with open('./pid.txt', 'w') as f:
        f.write('')


if __name__ == '__main__':
    _new_pid_file()
    _start_webserver()
    # app.run(host='0.0.0.0', port=config.PORT, processes=2)
