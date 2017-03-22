# !/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import render_template, Flask
app = Flask(__name__)

@app.route('/qr')
def get_QR():
    return render_template('qr.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port='1127')
