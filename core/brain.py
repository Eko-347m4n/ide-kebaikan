import pandas as pd
import numpy as np
import re
import os
import pickle
import random
import sys
import difflib 
import sqlite3
import json 
import csv
from datetime import datetime

# Import Rules
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
try:
    import rules
    print("✅ Rules loaded successfully.")
except ImportError:
    print("⚠️ FATAL: rules.py tidak ditemukan di folder core!")

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import KNeighborsClassifier
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, '../data/training_data.csv') 
LEARNED_PATH = os.path.join(BASE_DIR, '../data/learned_data.csv')
REJECTED_PATH = os.path.join(BASE_DIR, '../data/rejected_data.csv')
MODEL_PATH = os.path.join(BASE_DIR, 'trained_brain.pkl')

class BrainLogic:
    def __init__(self):
        print("🧠 Initializing Brain (Human-Centric + Plagiarism Guard)...")
        self.stemmer = StemmerFactory().create_stemmer()
        self.stopword_remover = StopWordRemoverFactory().create_stop_word_remover()
        
        self.vectorizer = None
        self.knn_level = None
        self.knn_quality = None
        self.is_trained = False
        self.init_learned_data()
        self.init_rejected_data()
        self.load_model()
        self.init_db() 

    def init_learned_data(self):
        """Membuat file learned_data.csv jika belum ada"""
        if not os.path.exists(LEARNED_PATH):
            try:
                os.makedirs(os.path.dirname(LEARNED_PATH), exist_ok=True)
                with open(LEARNED_PATH, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['text', 'target_level', 'quality']) # Header Standar
                print("📂 File 'learned_data.csv' baru berhasil dibuat.")
            except Exception as e:
                print(f"⚠️ Gagal membuat file learned data: {e}")
    
    def init_rejected_data(self):
        """[BARU] Membuat file rejected_data.csv jika belum ada"""
        if not os.path.exists(REJECTED_PATH):
            try:
                os.makedirs(os.path.dirname(REJECTED_PATH), exist_ok=True)
                with open(REJECTED_PATH, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['timestamp', 'text', 'reason']) # Header: Kapan, Apa, Kenapa
                print("📂 File 'rejected_data.csv' siap menampung sampah.")
            except Exception as e:
                print(f"⚠️ Gagal membuat file rejected data: {e}")

    def init_db(self):
        """Membuat tabel database jika belum ada"""
        db_path = os.path.join(BASE_DIR, '../data/kebaikan.db')
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        conn = sqlite3.connect(db_path)
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
        conn.close()
        print("🗄️ Database initialized.")

    def register_user(self, nama, kelas, encoding):
        db_path = os.path.join(BASE_DIR, '../data/kebaikan.db')
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        
        c.execute("SELECT id FROM siswa WHERE nama=? AND kelas=?", (nama, kelas))
        if c.fetchone():
            conn.close()
            return False, "Siswa sudah terdaftar!"
            
        encoding_list = encoding.tolist() 
        encoding_json = json.dumps(encoding_list)
        
        c.execute("INSERT INTO siswa (nama, kelas, encoding, total_poin) VALUES (?, ?, ?, 0)", 
                  (nama, kelas, encoding_json))
        conn.commit()
        conn.close()
        return True, "Pendaftaran Berhasil!"

    def add_points(self, nama, kelas, poin, ide, kategori_ide):
        db_path = os.path.join(BASE_DIR, '../data/kebaikan.db')
        conn = sqlite3.connect(db_path)
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
        conn.close()

    def get_leaderboard(self, limit=15):
        db_path = os.path.join(BASE_DIR, '../data/kebaikan.db')
        conn = sqlite3.connect(db_path)
        c = conn.cursor()        
        c.execute("SELECT nama, kelas, total_poin FROM siswa ORDER BY total_poin DESC LIMIT ?", (limit,))
        data = c.fetchall()         
        conn.close()
        return data
    
    def get_all_users(self):
        db_path = os.path.join(BASE_DIR, '../data/kebaikan.db')
        conn = sqlite3.connect(db_path)
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
        conn.close()
        return users
    
    def log_rejected_input(self, text, reason):
        """[BARU] Catat input yang ditolak ke CSV"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(REJECTED_PATH, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([timestamp, text, reason])
        except Exception as e:
            print(f"⚠️ Gagal mencatat rejection: {e}")

    def preprocess_text(self, text):
        if not isinstance(text, str): 
            return         
        text = text.lower()        
        text = re.sub(r'[^a-z\s]', ' ', text)      
        words = text.split()
        normalized_words = []
        for word in words:
            correct_word = rules.SLANG_DICTIONARY.get(word, word)
            normalized_words.append(correct_word)
        text = " ".join(normalized_words)
        text = self.stopword_remover.remove(text)        
        text = self.stemmer.stem(text)
        return text
    
    def train(self):
        print("📂 Loading datasets (Main + Learned)...")
        try:
            df_main = pd.read_csv(DATA_PATH)
            df_final = df_main
            if os.path.exists(LEARNED_PATH) and os.path.getsize(LEARNED_PATH) > 10:
                try:
                    df_learned = pd.read_csv(LEARNED_PATH)
                    print(f"📈 Menambahkan {len(df_learned)} data baru dari pengalaman lapangan.")
                    df_final = pd.concat([df_main, df_learned], ignore_index=True)
                except Exception as e:
                    print(f"⚠️ Warning: Gagal load learned_data, pakai data utama saja. Error: {e}")
            df_final.dropna(subset=['text', 'target_level', 'quality'], inplace=True)
            df_final['clean_text'] = df_final['text'].apply(self.preprocess_text)
            df_final = df_final[df_final['clean_text'].str.strip() != ""]
            self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
            X = self.vectorizer.fit_transform(df_final['clean_text'])
            self.knn_level = KNeighborsClassifier(n_neighbors=5, metric='cosine', weights='distance')
            self.knn_level.fit(X, df_final['target_level'])
            self.knn_quality = KNeighborsClassifier(n_neighbors=5, metric='cosine', weights='distance')
            self.knn_quality.fit(X, df_final['quality'])
            
            self.is_trained = True
            self.save_model()
            print(f"✅ Training Selesai! Total Data: {len(df_final)} baris.")
            
        except Exception as e:
            print(f"❌ Error Train: {e}")

    def auto_learn(self, text, level, quality):
        try:
            with open(LEARNED_PATH, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([text, level, quality])
            # print(f"📝 AI Belajar hal baru: '{text}' -> {level}") 
        except Exception as e:
            print(f"⚠️ Gagal menyimpan learned data: {e}")

    def calculate_score_saw(self, pred_level, pred_quality, text_len):
        W = [0.5, 0.3, 0.2]

        val_level = 0.0
        if pred_level in ['Friend', 'Self', 'Social']: val_level = 1.0
        elif pred_level == 'Enemy': val_level = 0.2
        else: val_level = 0.0 # Junk

        val_quality = 0.5 
        if pred_quality == 'Featured': val_quality = 1.0
        elif pred_quality == 'Exceptional': val_quality = 0.75
        elif pred_quality == 'Standard': val_quality = 0.5
   
        val_length = min(text_len / 100.0, 1.0)
        final_saw = (val_level * W[0]) + (val_quality * W[1]) + (val_length * W[2])
        
        score = int(round(final_saw * 10))
        
        return score
    
    def get_smart_feedback(self, text, category):
        text_lower = text.lower()
        
        category_bank = rules.FEEDBACK_BANK.get(category, {})
        
        if isinstance(category_bank, list):
            return random.choice(category_bank)
            
        selected_subcat = "default"
        
        if category in rules.CONTEXT_MAPPING:
            mapping = rules.CONTEXT_MAPPING[category]
            for keyword, subcat in mapping.items():
                if keyword in text_lower:
                    selected_subcat = subcat
                    break 
        
        feedback_options = category_bank.get(selected_subcat, category_bank.get("default", []))
        
        if not feedback_options: return "Terima kasih orang baik!" 
        
        return random.choice(feedback_options)
    
    def check_plagiarism(self, new_text, history_list):
        if not history_list: return False, None
        clean_new = new_text.lower().strip()
        for old_text in history_list:
            clean_old = old_text.lower().strip()
            if clean_new == clean_old:
                return True, old_text
            ratio = difflib.SequenceMatcher(None, clean_new, clean_old).ratio()
            if ratio > 0.85:
                return True, old_text
        return False, None

    def predict_and_score(self, text_input, class_history=[]):
        fail_response = {"success": False, "original_text": text_input, "msg": "Error", "debug": "Unknown"}
        if not self.is_trained:
            fail_response["msg"] = "Model belum siap."
            return fail_response

        text_lower = text_input.lower()
        clean_input = self.preprocess_text(text_input)
        
        if self.vectorizer.transform([clean_input]).sum() == 0:
            fail_response["msg"] = "Kalimat tidak dimengerti."
            self.log_rejected_input(text_input, "Unknown Words")
            return fail_response
        
        if len(text_input) < 10: 
            fail_response["msg"] = "Terlalu pendek."
            self.log_rejected_input(text_input, "Terlalu pendek")
            return fail_response
        
        if class_history:
            is_plagiat, _ = self.check_plagiarism(text_input, class_history)
            if is_plagiat: 
                fail_response["msg"] = "Ide mirip temanmu!"
                self.log_rejected_input(text_input, f"Plagiarism detected (Similiar to: {_})")
                return fail_response

        vec_input = self.vectorizer.transform([clean_input])
        pred_level = self.knn_level.predict(vec_input)[0]
        pred_quality = self.knn_quality.predict(vec_input)[0]
        confidence = np.max(self.knn_level.predict_proba(vec_input)) * 100
        
        if pred_level == "Junk": 
            fail_response["msg"] = "Kalimat kurang jelas/tidak nyambung."
            self.log_rejected_input(text_input, "Junk")
            return fail_response
        
        if pred_level == "Enemy":
            fail_response["msg"] = "Kebaikan harus positif ya!"
            self.log_rejected_input(text_input, "Enemy")
            return fail_response

        final_score = self.calculate_score_saw(pred_level, pred_quality, len(text_input))
        
        feedback_text = self.get_smart_feedback(text_input, pred_level)

        if pred_level in ['Friend', 'Self', 'Social'] and confidence > 60 and len(text_input) > 15:
            self.auto_learn(text_input, pred_level, pred_quality)

        return {
            "success": True,
            "original_text": text_input,
            "prediction_level": pred_level,
            "prediction_quality": pred_quality,
            "final_score": final_score,
            "feedback": feedback_text,
            "debug": f"Conf: {confidence:.0f}%"
        }

    def save_model(self):
        with open(MODEL_PATH, 'wb') as f:
            pickle.dump((self.vectorizer, self.knn_level, self.knn_quality), f)

    def load_model(self):
        if os.path.exists(MODEL_PATH):
            with open(MODEL_PATH, 'rb') as f:
                self.vectorizer, self.knn_level, self.knn_quality = pickle.load(f)
            self.is_trained = True
        else:
            print("⚠️ Model belum ada.")

# --- DEBUGGER S---
if __name__ == "__main__":
    brain = BrainLogic()
    brain.train()