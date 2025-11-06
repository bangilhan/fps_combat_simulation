"""
간단한 CSV to JSON 변환기 (표준 라이브러리만 사용)
"""
import csv
import json
from collections import defaultdict

def process_csv_to_json(csv_path, output_path):
    positions = []
    events = []
    
    # 플레이어 위치 데이터 저장용
    tick_data = {}
    current_tick = None
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            tick = int(row['tick']) if row['tick'] else None
            game_time = float(row['game_time']) if row['game_time'] else 0.0
            
            if tick is None:
                continue
                
            # 틱이 바뀌면 저장
            if current_tick != tick and current_tick is not None:
                positions.append({
                    'tick': current_tick,
                    'game_time': tick_data.get('game_time', 0),
                    'players': tick_data.get('players', [])
                })
                tick_data = {'players': []}
            
            current_tick = tick
            tick_data['game_time'] = game_time
            
            # 플레이어 위치 정보
            if row['X'] and row['Y'] and row['Z']:
                try:
                    player_info = {
                        'name': row['name'] or '',
                        'team': row['team_name'] or '',
                        'position': [
                            float(row['X']),
                            float(row['Z']),
                            float(row['Y'])
                        ],
                        'health': float(row['health']) if row['health'] else 100.0,
                        'round': int(row['round']) if row['round'] else 1
                    }
                    tick_data['players'].append(player_info)
                except (ValueError, KeyError):
                    pass
            
            # 킬 이벤트 처리
            if row['event']:
                try:
                    event = {
                        'tick': tick,
                        'game_time': game_time,
                        'event_type': row['event'],
                        'attacker': {
                            'name': row['attacker_name'] if row.get('attacker_name') else None,
                            'team': row['attacker_team_name'] if row.get('attacker_team_name') else None,
                            'position': [
                                float(row['attacker_X']) if row.get('attacker_X') and row['attacker_X'] else None,
                                float(row['attacker_Z']) if row.get('attacker_Z') and row['attacker_Z'] else None,
                                float(row['attacker_Y']) if row.get('attacker_Y') and row['attacker_Y'] else None
                            ],
                            'yaw': float(row['attacker_yaw']) if row.get('attacker_yaw') and row['attacker_yaw'] else None,
                            'pitch': float(row['attacker_pitch']) if row.get('attacker_pitch') and row['attacker_pitch'] else None,
                            'health': float(row['attacker_health']) if row.get('attacker_health') and row['attacker_health'] else None
                        },
                        'victim': {
                            'name': row['victim_name'] if row.get('victim_name') else None,
                            'team': row['victim_team_name'] if row.get('victim_team_name') else None,
                            'position': [
                                float(row['victim_X']) if row.get('victim_X') and row['victim_X'] else None,
                                float(row['victim_Z']) if row.get('victim_Z') and row['victim_Z'] else None,
                                float(row['victim_Y']) if row.get('victim_Y') and row['victim_Y'] else None
                            ],
                            'health': float(row['victim_health']) if row.get('victim_health') and row['victim_health'] else None
                        },
                        'weapon': row['weapon'] if row.get('weapon') else None,
                        'headshot': row['headshot'].lower() == 'true' if row.get('headshot') else False
                    }
                    events.append(event)
                except (ValueError, KeyError) as e:
                    pass
        
        # 마지막 틱 저장
        if current_tick is not None:
            positions.append({
                'tick': current_tick,
                'game_time': tick_data.get('game_time', 0),
                'players': tick_data.get('players', [])
            })
    
    # 메타데이터 생성
    game_times = [p['game_time'] for p in positions]
    ticks = [p['tick'] for p in positions]
    
    # 플레이어 목록 추출
    players = set()
    for pos in positions:
        for player in pos['players']:
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
        'players': list(players),
        'teams': ['CT', 'TERRORIST']
    }
    
    result = {
        'metadata': metadata,
        'positions': positions,
        'events': events
    }
    
    # JSON 저장
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"Processed {metadata['total_ticks']} ticks")
    print(f"Found {metadata['total_events']} events")
    print(f"Saved to {output_path}")
    
    return result

if __name__ == '__main__':
    process_csv_to_json('sample_dataset_kill_tick_info.csv', 'simulation_data.json')


