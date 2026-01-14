import sqlite3
import requests
import json
import os

# 保存先DBパス
DB_PATH = os.path.join(os.path.dirname(__file__), '../data/framedata.db')
# データソース (例: Smash DataのRaw JSONなど、信頼できるURLを指定)
# 実際には 'https://raw.githubusercontent.com/smashdata/smashdata/master/json/ultimate.json' などを使用
DATA_URL = "https://raw.githubusercontent.com/smashdata/smashdata/master/json/ultimate.json" 

def init_db():
    """データベースとテーブルの初期化"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 1. Characters Table (滞空F 4項目を追加済み)
    c.execute('''
        CREATE TABLE IF NOT EXISTS characters (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE,
            weight REAL,
            run_speed REAL,
            walk_speed REAL,
            air_speed REAL,
            fall_speed REAL,
            fast_fall_speed REAL,
            sh_air_time INTEGER,      -- 小J滞空F
            sh_ff_air_time INTEGER,   -- 小J急降下滞空F
            fh_air_time INTEGER,      -- 大J滞空F
            fh_ff_air_time INTEGER    -- 大J急降下滞空F
        )
    ''')

    # 2. Moves Table (計算用に整数化したデータを格納)
    c.execute('''
        CREATE TABLE IF NOT EXISTS moves (
            id INTEGER PRIMARY KEY,
            char_id INTEGER,
            move_name TEXT,
            input_type TEXT,
            startup INTEGER,          -- 最速発生F
            total_frames INTEGER,     -- 全体F
            landing_lag INTEGER,      -- 着地隙
            shield_advantage INTEGER, -- ガード硬直差
            base_damage REAL,
            note TEXT,                -- 特殊判定などのメモ
            FOREIGN KEY(char_id) REFERENCES characters(id)
        )
    ''')
    
    conn.commit()
    print("Database initialized.")
    return conn

def parse_frame(value):
    """ '3-5' や '6 (Late)' 等の文字列から最速F(整数)を抽出するヘルパー """
    if isinstance(value, int):
        return value
    if not value or value == '-':
        return None
    
    # 文字列の場合、最初の数字を取り出す簡易ロジック
    import re
    match = re.search(r'\d+', str(value))
    if match:
        return int(match.group())
    return None

def ingest_data(conn):
    """APIからデータを取得しDBへ格納"""
    print(f"Fetching data from {DATA_URL}...")
    try:
        response = requests.get(DATA_URL)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"Failed to fetch data: {e}")
        return

    c = conn.cursor()
    
    # キャラクターデータのループ (データ構造はソースのJSON形式に依存するため適宜調整)
    for char_key, char_data in data.get('fighters', {}).items():
        # キャラクター情報の挿入
        stats = char_data.get('stats', {})
        c.execute('''
            INSERT OR IGNORE INTO characters (
                name, weight, run_speed, walk_speed, air_speed, 
                fall_speed, fast_fall_speed, 
                sh_air_time, sh_ff_air_time, fh_air_time, fh_ff_air_time
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            char_data.get('name', char_key),
            stats.get('weight'),
            stats.get('run_speed'),
            stats.get('walk_speed'),
            stats.get('air_speed'),
            stats.get('fall_speed'),
            stats.get('fast_fall_speed'),
            # APIに該当キーがない場合はNoneが入る
            stats.get('sh_air_time'), 
            stats.get('sh_ff_air_time'),
            stats.get('fh_air_time'),
            stats.get('fh_ff_air_time')
        ))
        
        char_id = c.lastrowid
        if not char_id:
            # 既に存在する場合はIDを取得
            c.execute('SELECT id FROM characters WHERE name = ?', (char_data.get('name', char_key),))
            char_id = c.fetchone()[0]

        # 技データの挿入
        moves = char_data.get('moves', [])
        for move in moves:
            c.execute('''
                INSERT INTO moves (
                    char_id, move_name, input_type, 
                    startup, total_frames, landing_lag, shield_advantage, base_damage, note
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                char_id,
                move.get('name'),
                move.get('type'),
                parse_frame(move.get('startup')),       # 整数化
                parse_frame(move.get('totalFrames')),   # 整数化
                parse_frame(move.get('landingLag')),    # 整数化
                parse_frame(move.get('shieldAdvantage')), # 整数化
                move.get('baseDamage'),
                json.dumps(move) # 元データ全体をNoteとして保存しておく(念のため)
            ))

    conn.commit()
    print("Data ingestion complete.")

if __name__ == "__main__":
    conn = init_db()
    ingest_data(conn)
    conn.close()
