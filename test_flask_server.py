#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Flaskサーバーの動作確認用スクリプト
"""

from flask import Flask, render_template
from flask_socketio import SocketIO
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route('/')
def index():
    return render_template('pso_monitor.html')

@app.route('/test')
def test():
    return '<h1>Flask is working!</h1><p>Server is running on port 5000</p>'

if __name__ == '__main__':
    print("Starting Flask server...")
    print("Access the monitor at: http://localhost:5000")
    print("Test page at: http://localhost:5000/test")
    print("Press Ctrl+C to stop")
    
    # デバッグモードで起動（開発環境用）
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)