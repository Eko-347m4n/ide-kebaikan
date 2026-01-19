import sqlite3
import json
import os
from core.config import Config

class DatabaseManager:
    def __init__(self):
        self.db_path = Config.DB_PATH
        self.init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def init_db(self):
        """Membuat tabel database jika belum ada"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with self._get_connection() as conn:
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS siswa
                         (id INTEGER PRIMARY KEY AUTOINCREMENT,
                          nama TEXT, 
                          kelas TEXT, 
                          encoding TEXT, 
                          total_poin INTEGER DEFAULT 0, 
                          streak INTEGER DEFAULT 0, 
                          last_active DATE)''')
                          
            c.execute('''CREATE TABLE IF NOT EXISTS log_aktivitas
                         (id INTEGER PRIMARY KEY AUTOINCREMENT,
                          nama_siswa TEXT, 
                          kelas TEXT, 
                          ide_kebaikan TEXT, 
                          skor_ai INTEGER, 
                          kategori_ide TEXT,
                          waktu TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
            conn.commit()
        print("🗄️ Database initialized via DatabaseManager.")

    def register_user(self, nama, kelas, encoding):
        with self._get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT id FROM siswa WHERE nama=? AND kelas=?", (nama, kelas))
            if c.fetchone():
                return False, "Siswa sudah terdaftar!"
                
            encoding_list = encoding.tolist() if hasattr(encoding, 'tolist') else encoding
            encoding_json = json.dumps(encoding_list)
            
            c.execute("INSERT INTO siswa (nama, kelas, encoding, total_poin) VALUES (?, ?, ?, 0)", 
                      (nama, kelas, encoding_json))
            conn.commit()
            return True, "Pendaftaran Berhasil!"

    def add_points(self, nama, kelas, poin, ide, kategori_ide):
        with self._get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT id, total_poin FROM siswa WHERE nama=? AND kelas=?", (nama, kelas))
            data = c.fetchone()        
            if data:
                new_poin = data[1] + poin
                c.execute("UPDATE siswa SET total_poin=? WHERE id=?", (new_poin, data[0]))
            else:
                c.execute("INSERT INTO siswa (nama, kelas, total_poin) VALUES (?, ?, ?)", (nama, kelas, poin))
                
            c.execute("INSERT INTO log_aktivitas (nama_siswa, kelas, ide_kebaikan, skor_ai, kategori_ide) VALUES (?, ?, ?, ?, ?)", 
                      (nama, kelas, ide, poin, kategori_ide))
            conn.commit()

    def get_leaderboard(self, limit=15):
        with self._get_connection() as conn:
            c = conn.cursor()        
            c.execute("SELECT nama, kelas, total_poin FROM siswa ORDER BY total_poin DESC LIMIT ?", (limit,))
            return c.fetchall()

    def get_all_users(self):
        with self._get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT id, nama, kelas, encoding, total_poin FROM siswa")
            users = []
            for row in c.fetchall():
                if row[3]:
                    try:
                        encoding_list = json.loads(row[3])
                        users.append({
                            "id": row[0],
                            "nama": row[1],
                            "kelas": row[2],
                            "encoding": encoding_list,
                            "poin": row[4]
                        })
                    except:
                        pass
            return users
