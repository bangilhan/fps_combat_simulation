"""
Flask 웹 서버 - CSV를 직접 읽어서 처리 (전처리 불필요)
"""
from flask import Flask, render_template, jsonify
from flask_cors import CORS
import csv
import json
import os
from collections import defaultdict

app = Flask(__name__)
CORS(app)

# 캐시
_data_cache = None

def load_data_from_csv(csv_path='sample_dataset_kill_tick_info.csv'):
    """CSV를 직접 읽어서 데이터 반환"""
    global _data_cache
    
    if _data_cache is not None:
        return _data_cache
    
    print("CSV 파일 로딩 중...")
    positions = []
    events = []
    
    tick_data = {}
    current_tick = None
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for idx, row in enumerate(reader):
            if idx % 5000 == 0 and idx > 0:
                print(f"처리 중... {idx}줄")
            
            tick_str = row.get('tick', '').strip()
            if not tick_str:
                continue
                
            try:
                tick = int(tick_str)
                game_time = float(row.get('game_time', 0) or 0)
            except (ValueError, KeyError):
                continue
            
            # 틱이 바뀌면 저장
            if current_tick != tick and current_tick is not None and tick_data.get('players'):
                positions.append({
                    'tick': current_tick,
                    'game_time': tick_data.get('game_time', 0),
                    'players': tick_data.get('players', [])
                })
                tick_data = {'players': []}
            
            current_tick = tick
            tick_data['game_time'] = game_time
            
            # 플레이어 위치 정보
            x, y, z = row.get('X', '').strip(), row.get('Y', '').strip(), row.get('Z', '').strip()
            if x and y and z:
                try:
                    player_info = {
                        'name': row.get('name', '').strip(),
                        'team': row.get('team_name', '').strip(),
                        'position': [float(x), float(z), float(y)],
                        'health': float(row.get('health', 100) or 100),
                        'round': int(row.get('round', 1) or 1)
                    }
                    if player_info['name']:
                        tick_data.setdefault('players', []).append(player_info)
                except (ValueError, KeyError):
                    pass
            
            # 킬 이벤트
            event = row.get('event', '').strip()
            if event:
                try:
                    event_data = {
                        'tick': tick,
                        'game_time': game_time,
                        'event_type': event,
                        'attacker': {
                            'name': row.get('attacker_name', '').strip() or None,
                            'team': row.get('attacker_team_name', '').strip() or None,
                            'position': [
                                float(row['attacker_X']) if row.get('attacker_X') and row['attacker_X'].strip() else None,
                                float(row['attacker_Z']) if row.get('attacker_Z') and row['attacker_Z'].strip() else None,
                                float(row['attacker_Y']) if row.get('attacker_Y') and row['attacker_Y'].strip() else None
                            ],
                            'yaw': float(row['attacker_yaw']) if row.get('attacker_yaw') and row['attacker_yaw'].strip() else None,
                            'pitch': float(row['attacker_pitch']) if row.get('attacker_pitch') and row['attacker_pitch'].strip() else None,
                            'health': float(row['attacker_health']) if row.get('attacker_health') and row['attacker_health'].strip() else None
                        },
                        'victim': {
                            'name': row.get('victim_name', '').strip() or None,
                            'team': row.get('victim_team_name', '').strip() or None,
                            'position': [
                                float(row['victim_X']) if row.get('victim_X') and row['victim_X'].strip() else None,
                                float(row['victim_Z']) if row.get('victim_Z') and row['victim_Z'].strip() else None,
                                float(row['victim_Y']) if row.get('victim_Y') and row['victim_Y'].strip() else None
                            ],
                            'health': float(row['victim_health']) if row.get('victim_health') and row['victim_health'].strip() else None
                        },
                        'weapon': row.get('weapon', '').strip() or None,
                        'headshot': row.get('headshot', '').strip().lower() == 'true'
                    }
                    events.append(event_data)
                except (ValueError, KeyError):
                    pass
        
        # 마지막 틱
        if current_tick is not None and tick_data.get('players'):
            positions.append({
                'tick': current_tick,
                'game_time': tick_data.get('game_time', 0),
                'players': tick_data.get('players', [])
            })
    
    # 메타데이터
    game_times = [p['game_time'] for p in positions if p.get('game_time')]
    ticks = [p['tick'] for p in positions if p.get('tick')]
    
    players = set()
    for pos in positions:
        for player in pos.get('players', []):
            if player.get('name'):
                players.add(player['name'])
    
    metadata = {
        'total_ticks': len(positions),
        'total_events': len(events),
        'time_range': {
            'min': min(game_times) if game_times else 0,
            'max': max(game_times) if game_times else 0
        },
        'tick_range': {
            'min': min(ticks) if ticks else 0,
            'max': max(ticks) if ticks else 0
        },
        'players': sorted(list(players)),
        'teams': ['CT', 'TERRORIST']
    }
    
    _data_cache = {
        'metadata': metadata,
        'positions': positions,
        'events': events
    }
    
    print(f"로딩 완료! {len(positions)} 틱, {len(events)} 이벤트")
    return _data_cache

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/data')
def get_data():
    """전체 시뮬레이션 데이터 반환"""
    data = load_data_from_csv()
    return jsonify(data)

@app.route('/api/positions')
def get_positions():
    """플레이어 위치 데이터만 반환"""
    data = load_data_from_csv()
    return jsonify(data.get('positions', []))

@app.route('/api/events')
def get_events():
    """이벤트 데이터만 반환"""
    data = load_data_from_csv()
    return jsonify(data.get('events', []))

@app.route('/api/metadata')
def get_metadata():
    """메타데이터만 반환"""
    data = load_data_from_csv()
    return jsonify(data.get('metadata', {}))

if __name__ == '__main__':
    print("서버 시작 중...")
    print("CSV 파일을 처음 로드할 때 시간이 걸릴 수 있습니다.")
    app.run(debug=True, port=5000, threaded=True)


