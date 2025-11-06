"""
CSV 데이터를 처리하여 3D 시뮬레이션에 필요한 형태로 변환
"""
import pandas as pd
import json
from typing import Dict, List, Tuple

class DataProcessor:
    def __init__(self, csv_path: str):
        self.df = pd.read_csv(csv_path)
        self.processed_data = None
        
    def process(self) -> Dict:
        """데이터를 처리하여 JSON 형태로 반환"""
        # 킬 이벤트가 있는 행만 필터링
        kill_events = self.df[self.df['event'].notna()].copy()
        
        # 플레이어 위치 데이터 (모든 틱)
        player_positions = []
        current_tick = None
        tick_data = {}
        
        for _, row in self.df.iterrows():
            tick = int(row['tick'])
            game_time = float(row['game_time'])
            
            if current_tick != tick:
                if current_tick is not None:
                    player_positions.append({
                        'tick': current_tick,
                        'game_time': tick_data.get('game_time', 0),
                        'players': tick_data.get('players', [])
                    })
                current_tick = tick
                tick_data = {
                    'game_time': game_time,
                    'players': []
                }
            
            # 플레이어 정보 추가
            if pd.notna(row['X']) and pd.notna(row['Y']) and pd.notna(row['Z']):
                player_info = {
                    'name': str(row['name']),
                    'team': str(row['team_name']),
                    'position': [float(row['X']), float(row['Z']), float(row['Y'])],  # X, Y, Z를 3D 좌표로 (Y는 높이)
                    'health': float(row['health']) if pd.notna(row['health']) else 100.0,
                    'round': int(row['round']) if pd.notna(row['round']) else 1
                }
                tick_data['players'].append(player_info)
        
        # 마지막 틱 추가
        if current_tick is not None:
            player_positions.append({
                'tick': current_tick,
                'game_time': tick_data.get('game_time', 0),
                'players': tick_data.get('players', [])
            })
        
        # 킬 이벤트 처리
        events = []
        for _, row in kill_events.iterrows():
            event = {
                'tick': int(row['tick']),
                'game_time': float(row['game_time']),
                'event_type': str(row['event']),
                'attacker': {
                    'name': str(row['attacker_name']) if pd.notna(row['attacker_name']) else None,
                    'team': str(row['attacker_team_name']) if pd.notna(row['attacker_team_name']) else None,
                    'position': [
                        float(row['attacker_X']) if pd.notna(row['attacker_X']) else None,
                        float(row['attacker_Z']) if pd.notna(row['attacker_Z']) else None,
                        float(row['attacker_Y']) if pd.notna(row['attacker_Y']) else None
                    ],
                    'yaw': float(row['attacker_yaw']) if pd.notna(row['attacker_yaw']) else None,
                    'pitch': float(row['attacker_pitch']) if pd.notna(row['attacker_pitch']) else None,
                    'health': float(row['attacker_health']) if pd.notna(row['attacker_health']) else None
                },
                'victim': {
                    'name': str(row['victim_name']) if pd.notna(row['victim_name']) else None,
                    'team': str(row['victim_team_name']) if pd.notna(row['victim_team_name']) else None,
                    'position': [
                        float(row['victim_X']) if pd.notna(row['victim_X']) else None,
                        float(row['victim_Z']) if pd.notna(row['victim_Z']) else None,
                        float(row['victim_Y']) if pd.notna(row['victim_Y']) else None
                    ],
                    'health': float(row['victim_health']) if pd.notna(row['victim_health']) else None
                },
                'weapon': str(row['weapon']) if pd.notna(row['weapon']) else None,
                'headshot': bool(row['headshot']) if pd.notna(row['headshot']) else False
            }
            events.append(event)
        
        # 메타데이터
        metadata = {
            'total_ticks': len(player_positions),
            'total_events': len(events),
            'time_range': {
                'min': float(self.df['game_time'].min()),
                'max': float(self.df['game_time'].max())
            },
            'tick_range': {
                'min': int(self.df['tick'].min()),
                'max': int(self.df['tick'].max())
            },
            'players': list(self.df['name'].unique()),
            'teams': list(self.df['team_name'].unique())
        }
        
        return {
            'metadata': metadata,
            'positions': player_positions,
            'events': events
        }
    
    def save_json(self, output_path: str):
        """처리된 데이터를 JSON 파일로 저장"""
        data = self.process()
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return data

if __name__ == '__main__':
    processor = DataProcessor('sample_dataset_kill_tick_info.csv')
    data = processor.save_json('simulation_data.json')
    print(f"Processed {data['metadata']['total_ticks']} ticks")
    print(f"Found {data['metadata']['total_events']} events")


