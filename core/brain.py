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
        
        # Tabel Siswa (Menyimpan Poin & Wajah)
        c.execute('''CREATE TABLE IF NOT EXISTS siswa
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      nama TEXT, 
                      kelas TEXT, 
                      encoding TEXT, 
                      total_poin INTEGER DEFAULT 0, 
                      streak INTEGER DEFAULT 0, 
                      last_active DATE)''')
                      
        # Tabel Log (Riwayat Kebaikan)
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
        """Mendaftarkan siswa baru beserta data wajahnya"""
        db_path = os.path.join(BASE_DIR, '../data/kebaikan.db')
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        
        # Cek apakah sudah ada (berdasarkan Nama & Kelas)
        c.execute("SELECT id FROM siswa WHERE nama=? AND kelas=?", (nama, kelas))
        if c.fetchone():
            conn.close()
            return False, "Siswa sudah terdaftar!"
            
        # Simpan encoding wajah sebagai JSON String
        encoding_list = encoding.tolist() # Convert numpy array ke list
        encoding_json = json.dumps(encoding_list)
        
        c.execute("INSERT INTO siswa (nama, kelas, encoding, total_poin) VALUES (?, ?, ?, 0)", 
                  (nama, kelas, encoding_json))
        conn.commit()
        conn.close()
        return True, "Pendaftaran Berhasil!"

    def add_points(self, nama, kelas, poin, ide, kategori_ide):
        """Menambahkan poin ke siswa dan mencatat log"""
        db_path = os.path.join(BASE_DIR, '../data/kebaikan.db')
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        
        # 1. Update/Insert Siswa
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
        """Mengambil Top 5 Siswa dengan Poin Tertinggi"""
        db_path = os.path.join(BASE_DIR, '../data/kebaikan.db')
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        
        c.execute("SELECT nama, kelas, total_poin FROM siswa ORDER BY total_poin DESC LIMIT ?", (limit,))
        data = c.fetchall() 
        
        conn.close()
        return data
    
    def get_all_users(self):
        """Mengambil semua data siswa + encoding wajah untuk Vision System"""
        import json # Pastikan import json
        db_path = os.path.join(BASE_DIR, '../data/kebaikan.db')
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        
        c.execute("SELECT id, nama, kelas, encoding, total_poin FROM siswa")
        users = []
        for row in c.fetchall():
            if row[3]: # Jika ada encoding
                try:
                    # Encoding disimpan sebagai list di DB, tapi format teks
                    # Kita ubah jadi List Python pakai json.loads
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
        if not isinstance(text, str): return ""
        
        # 1. Lowercase
        text = text.lower()
        
        # 2. Hapus angka/simbol
        text = re.sub(r'[^a-z\s]', ' ', text)
        
        # 3. Slang Correction (BAHASA GAUL -> BAKU)
        # Pisahkan kalimat jadi kata-kata
        words = text.split()
        normalized_words = []
        for word in words:
            # Cek di kamus rules, kalau ada ganti, kalau ga ada biarin
            correct_word = rules.SLANG_DICTIONARY.get(word, word)
            normalized_words.append(correct_word)
        text = " ".join(normalized_words)

        # 4. Stopword Removal (Hapus: yang, di, ke...)
        text = self.stopword_remover.remove(text)
        
        # 5. Stemming (membantu -> bantu)
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

    def calculate_score(self, pred_level, pred_quality, text_len):
        if pred_level == 'Junk': return 0
        if pred_level == 'Enemy': return 5 
        
        quality_map = {'Standard': 10, 'Exceptional': 20, 'Featured': 40}
        score = quality_map.get(pred_quality, 10)
        
        if pred_quality == 'Standard' and text_len > 35:
            score += 5
            
        return score
    
    def get_smart_feedback(self, text, category):
        """
        Memilih feedback berdasarkan konteks kata kunci di input.
        """
        text_lower = text.lower()
        
        # Ambil Bank Feedback untuk kategori ini
        category_bank = rules.FEEDBACK_BANK.get(category, {})
        
        # Jika bank-nya list biasa (fallback legacy), ambil random
        if isinstance(category_bank, list):
            return random.choice(category_bank)
            
        # Jika bank-nya Dictionary (Smart Mode), cari sub-kategori
        selected_subcat = "default"
        
        # Cek Mapping di Rules (misal: "tidur" -> subcat "tidur")
        if category in rules.CONTEXT_MAPPING:
            mapping = rules.CONTEXT_MAPPING[category]
            for keyword, subcat in mapping.items():
                if keyword in text_lower:
                    selected_subcat = subcat
                    break # Ketemu satu aja cukup
        
        # Ambil list feedback dari sub-kategori yg dipilih
        feedback_options = category_bank.get(selected_subcat, category_bank.get("default", []))
        
        if not feedback_options: return "Terima kasih orang baik!" # Safety net
        
        return random.choice(feedback_options)
    
    # --- FITUR BARU: PLAGIARISM CHECKER ---
    def check_plagiarism(self, new_text, history_list):
        """
        Mengecek apakah new_text mirip dengan salah satu kalimat di history_list.
        Return: (Boolean IsPlagiat, Kalimat Asli yang Dicontek)
        """
        if not history_list: return False, None
        
        clean_new = new_text.lower().strip()
        
        for old_text in history_list:
            clean_old = old_text.lower().strip()
            
            # 1. Cek Exact Match (Cepat)
            if clean_new == clean_old:
                return True, old_text
            
            # 2. Cek Fuzzy Match (Agak Lambat tapi Akurat)
            # Rasio > 0.85 artinya 85% mirip (misal cuma beda 1-2 kata)
            ratio = difflib.SequenceMatcher(None, clean_new, clean_old).ratio()
            if ratio > 0.85:
                return True, old_text
                
        return False, None

# --- MAIN PREDICTION (ROBUST VERSION) ---
    def predict_and_score(self, text_input, class_history=[]):
        # Default Fail Response (Safety Net)
        fail_response = {"success": False, "original_text": text_input, "msg": "Error", "debug": "Unknown"}

        if not self.is_trained:
            fail_response["msg"] = "Model belum siap. Train dulu."
            return fail_response

        text_lower = text_input.lower()
        clean_input = self.preprocess_text(text_input)
        
        # Layer 0: Gibberish
        if self.vectorizer.transform([clean_input]).sum() == 0:
            fail_response["msg"] = "AI tidak mengerti kalimat ini."
            fail_response["debug"] = "Zero Vector"
            return fail_response

        # Layer 1: Rules Basic
        if len(text_input) < 10: 
            fail_response["msg"] = "Terlalu pendek."
            return fail_response
        
        bad_hit = [w for w in rules.BAD_KEYWORDS if w in text_lower]
        if bad_hit:
            if not any(w in text_lower for w in rules.GOOD_CONTEXT_FOR_BAD_WORDS):
                fail_response["msg"] = f"⚠️ Terdeteksi kata: '{bad_hit[0]}'."
                fail_response["debug"] = "Bad Word"
                return fail_response

        # Layer 1.5: Plagiarism
        if class_history:
            is_plagiat, _ = self.check_plagiarism(text_input, class_history)
            if is_plagiat: 
                fail_response["msg"] = "Ide ini mirip temanmu!"
                fail_response["debug"] = "Plagiarism"
                return fail_response

        # Layer 2: Override
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

        # Layer 3: AI
        vec_input = self.vectorizer.transform([clean_input])
        pred_level = self.knn_level.predict(vec_input)[0]
        pred_quality = self.knn_quality.predict(vec_input)[0]
        confidence = np.max(self.knn_level.predict_proba(vec_input)) * 100
        
        if forced_level: pred_level = forced_level
        elif pred_level == "Junk": 
            fail_response["msg"] = "AI bingung (Kategori Junk)."
            fail_response["debug"] = "Junk Predicted"
            return fail_response

        # Layer 4: Output
        final_score = self.calculate_score(pred_level, pred_quality, len(text_input))
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

if __name__ == "__main__":
    brain = BrainLogic()
    # PENTING: Jalankan training jika error "Model belum siap"
    # print("🚀 TRAINING ULANG...")
    # brain.train() 
    
    print("\n--- TEST SMART FEEDBACK ---")
    
    cases = [
        "Saya mau tidur siang dulu capek", # Self - Istirahat
        "Saya makan bakso biar kenyang",   # Self - Makan
        "Saya membantu teman belajar",     # Friend - Bantu
        "asdfg",                           # Fail - Zero Vector
    ]

    for txt in cases:
        res = brain.predict_and_score(txt)
        print(f"\nInput: {res.get('original_text', txt)}") # Pakai .get() biar aman
        
        if res['success']:
            print(f"✅ Kategori: {res['prediction_level']}")
            print(f"   Feedback: {res['feedback']}")
        else:
            print(f"❌ Error: {res['msg']}")
            if 'debug' in res: print(f"   Debug: {res['debug']}")