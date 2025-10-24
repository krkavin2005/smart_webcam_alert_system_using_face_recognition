import sqlite3, os
from datetime import datetime

BASE_DIR=os.path.dirname(os.path.abspath(__file__))
DB_FILE=os.path.abspath(os.path.join(BASE_DIR,"..","Logs","intruder_log.db"))

def init_db():
    os.makedirs(os.path.dirname(DB_FILE),exist_ok=True)
    conn=sqlite3.connect(DB_FILE)
    c=conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS logs(
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              name TEXT,
              status TEXT,
              snapshot TEXT,
              timestamp TEXT)""")
    conn.commit();conn.close()

def log_event(name,status,snapshot_path=None):
    conn =sqlite3.connect(DB_FILE)
    c=conn.cursor()
    c.execute("INSERT INTO logs (name,status,snapshot,timestamp) VALUES (?,?,?,?)",(name,status,snapshot_path,datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()