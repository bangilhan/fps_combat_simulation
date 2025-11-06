"""
빠른 CSV to JSON 변환기 (최적화 버전)
"""
import csv
import json
from collections import defaultdict

def process_csv_to_json(csv_path, output_path, sample_ratio=1):
    """
    sample_ratio: 1 = 전체, 0.1 = 10%만, 0.5 = 50%만
    """
    positions = []
    events = []
    
    tick_data = {}
    current_tick = None
    processed_count = 0
    
    print("CSV 파일 읽는 중...")
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for idx, row in enumerate(reader):
            # 샘플링 (빠른 테스트용)
            if sample_ratio < 1 and idx % int(1/sample_ratio) != 0:
                continue
                
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
            
            # 플레이어 위치 정보 (값이 있는 경우만)
            x, y, z = row.get('X', ''), row.get('Y', ''), row.get('Z', '')
            if x and y and z:
                try:
                    player_info = {
                        'name': row.get('name', '').strip(),
                        'team': row.get('team_name', '').strip(),
                        'position': [float(x), float(z), float(y)],  # X, Z, Y 순서
                        'health': float(row.get('health', 100) or 100),
                        'round': int(row.get('round', 1) or 1)
                    }
                    if player_info['name']:  # 이름이 있는 경우만 추가
                        tick_data.setdefault('players', []).append(player_info)
                except (ValueError, KeyError):
                    pass
            
            # 킬 이벤트 처리
            event = row.get('event', '').strip()
            if event:
                try:
                    attacker_x = row.get('attacker_X', '').strip()
                    attacker_y = row.get('attacker_Y', '').strip()
                    attacker_z = row.get('attacker_Z', '').strip()
                    
                    event_data = {
                        'tick': tick,
                        'game_time': game_time,
                        'event_type': event,
                        'attacker': {
                            'name': row.get('attacker_name', '').strip() or None,
                            'team': row.get('attacker_team_name', '').strip() or None,
                            'position': [
                                float(attacker_x) if attacker_x else None,
                                float(attacker_z) if attacker_z else None,
                                float(attacker_y) if attacker_y else None
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
                except (ValueError, KeyError) as e:
                    pass
            
            processed_count += 1
            if processed_count % 10000 == 0:
                print(f"처리 중... {processed_count}줄")
        
        # 마지막 틱 저장
        if current_tick is not None and tick_data.get('players'):
            positions.append({
                'tick': current_tick,
                'game_time': tick_data.get('game_time', 0),
                'players': tick_data.get('players', [])
            })
    
    print(f"데이터 처리 완료: {len(positions)} 틱, {len(events)} 이벤트")
    
    # 메타데이터 생성
    game_times = [p['game_time'] for p in positions if p.get('game_time')]
    ticks = [p['tick'] for p in positions if p.get('tick')]
    
    # 플레이어 목록 추출
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
    
    result = {
        'metadata': metadata,
        'positions': positions,
        'events': events
    }
    
    print("JSON 파일 저장 중...")
    # JSON 저장 (압축 없이)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=None, separators=(',', ':'), ensure_ascii=False)
    
    print(f"완료! {output_path}에 저장됨")
    print(f"- 총 틱: {metadata['total_ticks']}")
    print(f"- 총 이벤트: {metadata['total_events']}")
    print(f"- 플레이어: {len(metadata['players'])}명")
    
    return result

if __name__ == '__main__':
    import sys
    # 빠른 테스트를 위해 10%만 처리 (전체를 원하면 1로 변경)
    sample = 1.0  # 전체 처리
    if len(sys.argv) > 1:
        sample = float(sys.argv[1])
    
    process_csv_to_json('sample_dataset_kill_tick_info.csv', 'simulation_data.json', sample)


