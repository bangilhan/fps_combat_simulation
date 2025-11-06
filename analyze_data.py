import pandas as pd
import numpy as np

# CSV 파일 읽기
df = pd.read_csv('sample_dataset_kill_tick_info.csv')

# 킬 이벤트가 있는 행 찾기
kill_events = df[df['event'].notna()]
print(f"Total rows: {len(df)}")
print(f"Rows with kill events: {len(kill_events)}")
print("\nSample kill event:")
print(kill_events.head(1).to_dict())

# 고유한 플레이어들
print("\nUnique players:")
print(df['name'].unique())

# 시간 범위
print(f"\nTime range: {df['game_time'].min()} - {df['game_time'].max()}")
print(f"Tick range: {df['tick'].min()} - {df['tick'].max()}")

# 위치 범위
print(f"\nX range: {df['X'].min()} - {df['X'].max()}")
print(f"Y range: {df['Y'].min()} - {df['Y'].max()}")
print(f"Z range: {df['Z'].min()} - {df['Z'].max()}")


