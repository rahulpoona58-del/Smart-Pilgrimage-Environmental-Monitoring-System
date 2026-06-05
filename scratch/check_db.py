import sqlite3

def check():
    conn = sqlite3.connect('database/buffer.db')
    cursor = conn.cursor()
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='sensor_data'")
    row = cursor.fetchone()
    if row:
        print("sensor_data:", row[0])
    
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='disaster_alerts'")
    row = cursor.fetchone()
    if row:
        print("disaster_alerts:", row[0])

if __name__ == "__main__":
    check()
