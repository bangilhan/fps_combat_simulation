"""
Flask 웹 서버 - 3D 시뮬레이션 데이터 제공
"""
from flask import Flask, render_template, jsonify
from flask_cors import CORS
import json
import os

app = Flask(__name__)
CORS(app)

# 데이터 로드
SIMULATION_DATA = None

def load_data():
    global SIMULATION_DATA
    if os.path.exists('simulation_data.json'):
        with open('simulation_data.json', 'r', encoding='utf-8') as f:
            SIMULATION_DATA = json.load(f)
    return SIMULATION_DATA

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/data')
def get_data():
    """전체 시뮬레이션 데이터 반환"""
    if SIMULATION_DATA is None:
        load_data()
    return jsonify(SIMULATION_DATA)

@app.route('/api/positions')
def get_positions():
    """플레이어 위치 데이터만 반환"""
    if SIMULATION_DATA is None:
        load_data()
    return jsonify(SIMULATION_DATA.get('positions', []))

@app.route('/api/events')
def get_events():
    """이벤트 데이터만 반환"""
    if SIMULATION_DATA is None:
        load_data()
    return jsonify(SIMULATION_DATA.get('events', []))

@app.route('/api/metadata')
def get_metadata():
    """메타데이터만 반환"""
    if SIMULATION_DATA is None:
        load_data()
    return jsonify(SIMULATION_DATA.get('metadata', {}))

if __name__ == '__main__':
    load_data()
    app.run(debug=True, port=5000)


