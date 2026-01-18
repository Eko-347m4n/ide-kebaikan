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
MODEL_PATH = os.path.join(BASE_DIR, 'trained_brain.pkl')

class BrainLogic:

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
        
        # Cek apakah sudah ada (berdasarkan Nama & Kelas)
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
            
        # 2. Catat Log Aktivitas
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
        import json # Pastikan import json
        db_path = os.path.join(BASE_DIR, '../data/kebaikan.db')
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        
        c.execute("SELECT id, nama, kelas, encoding, total_poin FROM siswa")
        users = []
        for row in c.fetchall():
            if row[3]: # Jika ada encoding
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
    
    def __init__(self):
        print("🧠 Initializing Brain (Human-Centric + Plagiarism Guard)...")
        self.stemmer = StemmerFactory().create_stemmer()
        self.stopword_remover = StopWordRemoverFactory().create_stop_word_remover()
        
        self.vectorizer = None
        self.knn_level = None
        self.knn_quality = None
        self.is_trained = False
        self.load_model()
        self.init_db()

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
    
    def train(self, data_path=DATA_PATH):
        print(f"📂 Loading dataset from {data_path}...")
        try:
            df = pd.read_csv(data_path)
            df.dropna(subset=['text', 'target_level', 'quality'], inplace=True)
        except:
            print("❌ Dataset tidak ditemukan!")
            return

        print("🧹 Preprocessing data...")
        df['clean_text'] = df['text'].apply(self.preprocess_text)
        df = df[df['clean_text'].str.strip() != ""]

        print("🤖 Training KNN Models...")
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
        X = self.vectorizer.fit_transform(df['clean_text'])

        self.knn_level = KNeighborsClassifier(n_neighbors=5, metric='cosine', weights='distance')
        self.knn_level.fit(X, df['target_level'])
        
        self.knn_quality = KNeighborsClassifier(n_neighbors=5, metric='cosine', weights='distance')
        self.knn_quality.fit(X, df['quality'])

        self.is_trained = True
        print("✅ Training Selesai!")
        self.save_model()

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
            fail_response["msg"] = "Model belum siap. Train dulu."
            return fail_response

        text_lower = text_input.lower()
        clean_input = self.preprocess_text(text_input)
        
        if self.vectorizer.transform([clean_input]).sum() == 0:
            fail_response["msg"] = "AI tidak mengerti kalimat ini."
            fail_response["debug"] = "Zero Vector"
            return fail_response

        if len(text_input) < 10: 
            fail_response["msg"] = "Terlalu pendek."
            return fail_response
        
        bad_hit = [w for w in rules.BAD_KEYWORDS if w in text_lower]
        if bad_hit:
            if not any(w in text_lower for w in rules.GOOD_CONTEXT_FOR_BAD_WORDS):
                fail_response["msg"] = f"⚠️ Terdeteksi kata: '{bad_hit[0]}'."
                fail_response["debug"] = "Bad Word"
                return fail_response

        if class_history:
            is_plagiat, _ = self.check_plagiarism(text_input, class_history)
            if is_plagiat: 
                fail_response["msg"] = "Ide ini mirip temanmu!"
                fail_response["debug"] = "Plagiarism"
                return fail_response

        forced_level = None
        debug_reason = "Pure AI"
        
        if any(w in text_lower for w in rules.BLOCK_KEYWORDS):
             if not any(w in text_lower for w in rules.HUMAN_KEYWORDS):
                 fail_response["msg"] = "Fokus ke teman sekelas ya!"
                 fail_response["debug"] = "Env Rejected"
                 return fail_response

        if any(w in text_lower for w in rules.SELF_KEYWORDS):
            forced_level = "Self"
            debug_reason = "Rule: Self"
        elif any(w in text_lower for w in rules.SOCIAL_VIP_KEYWORDS):
            forced_level = "Friend"
            debug_reason = "Rule: VIP"

        vec_input = self.vectorizer.transform([clean_input])
        pred_level = self.knn_level.predict(vec_input)[0]
        pred_quality = self.knn_quality.predict(vec_input)[0]
        confidence = np.max(self.knn_level.predict_proba(vec_input)) * 100
        
        if forced_level: pred_level = forced_level
        elif pred_level == "Junk": 
            fail_response["msg"] = "AI bingung (Kategori Junk)."
            fail_response["debug"] = "Junk Predicted"
            return fail_response

        final_score = self.calculate_score_saw(pred_level, pred_quality, len(text_input))
        feedback_text = self.get_smart_feedback(text_input, pred_level)

        return {
            "success": True,
            "original_text": text_input,
            "prediction_level": pred_level,
            "prediction_quality": pred_quality,
            "final_score": final_score,
            "feedback": feedback_text,
            "debug": f"{debug_reason} ({confidence:.0f}%)"
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