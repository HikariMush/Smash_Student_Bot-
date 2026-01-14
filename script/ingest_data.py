import sqlite3
import requests
import json

# DB初期化
def init_db():
    conn = sqlite3.connect('../data/framedata.db')
    c = conn.cursor()
    
    # キャラクターテーブル（ジャンプF追加版）
    c.execute('''CREATE TABLE IF NOT EXISTS characters
                 (id INTEGER PRIMARY KEY, name TEXT, weight REAL, 
                  run_speed REAL, walk_speed REAL, air_speed REAL, 
                  fall_speed REAL, fast_fall_speed REAL,
                  sh_air_time INTEGER, sh_ff_air_time INTEGER,
                  fh_air_time INTEGER, fh_ff_air_time INTEGER)''')

    # 技テーブル（最速発生F格納）
    c.execute('''CREATE TABLE IF NOT EXISTS moves
                 (id INTEGER PRIMARY KEY, char_id INTEGER, move_name TEXT, 
                  input_type TEXT, startup INTEGER, total_frames INTEGER, 
                  landing_lag INTEGER, shield_advantage INTEGER, base_damage REAL,
                  note TEXT,
                  FOREIGN KEY(char_id) REFERENCES characters(id))''')
    
    conn.commit()
    return conn

# データ取得 & 格納 (擬似コード)
def ingest_data(conn):
    # 想定: UFD等の非公式APIのエンドポイント
    chars_url = "https://api.ultimateframedata.com/stats" 
    
    # ※実際はAPIのレスポンス形式に合わせてパース処理を書きます
    # response = requests.get(chars_url).json()
    
    # 取得したデータをDBにINSERTする処理
    # ...
    
    print("Database built successfully.")

if __name__ == "__main__":
    conn = init_db()
    ingest_data(conn)
    conn.close()
