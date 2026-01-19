import cv2
import dlib
import numpy as np
import os
import face_recognition # Tetap butuh ini utk encoding login awal

from core.config import Config

class VisionSystem:
    def __init__(self):
        
        # --- 1. SETUP MODEL DLIB ---
        model_path = Config.DLIB_MODEL_PATH
        
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"❌ ERROR: File '{model_path}' hilang!")
        
        self.detector = dlib.get_frontal_face_detector()
        self.predictor = dlib.shape_predictor(model_path)

        # --- 2. DATABASE & CONFIG ---
        self.memory_users = []
        self.memory_encodings = []
        
        self.ZONE_GREEN = Config.ZONE_GREEN
        self.ZONE_YELLOW = Config.ZONE_YELLOW
        
        # --- 3. KONFIGURASI SENYUM (DARI KODE BARUMU) ---
        self.LIP_JAW_THRESHOLD = Config.LIP_JAW_THRESHOLD
        
        # Rasio Bukaan Mulut dibagi Jarak Hidung-Mulut
        self.OPENING_THRESHOLD = Config.OPENING_THRESHOLD

        # --- 4. OPTIMASI ---
        self.frame_count = 0
        self.SKIP_FRAMES = Config.SKIP_FRAMES
        self.RESIZE_FACTOR = Config.RESIZE_FACTOR
        
        # Stabilizer
        self.avg_ratio = 0.0
        self.alpha = 0.3

        self.last_result = {
            "face_detected": False, "is_smiling": False, "smile_score": 0.0,
            "zone": "RED", "user_data": None, "distance": 1.0, "location": None
        }

    def load_memory(self, users_data):
        self.memory_users = []
        self.memory_encodings = []
        for user in users_data:
            if user['encoding']:
                try:
                    self.memory_encodings.append(np.array(user["encoding"]))
                    self.memory_users.append(user)
                except: pass

    def calculate_smile_hybrid(self, shape):
        """
        Mengkombinasikan logika Lip-Jaw Ratio (Kode Kamu) 
        dengan struktur data Dlib (Kode Saya).
        """
        # Helper: Ambil koordinat (x, y) dari titik ke-n
        def pt(n): return np.array([shape.part(n).x, shape.part(n).y])
        def dist(a, b): return np.linalg.norm(a - b)

        # 1. Hitung Lebar Bibir (Ujung 48 ke 54)
        lips_width = dist(pt(48), pt(54))

        # 2. Hitung Lebar Rahang (Titik 2 ke 14 - Pipi ke Pipi)
        # Note: Di model 68 titik, rahang itu 0-16. 
        # Titik 2 dan 14 adalah sudut rahang yang pas untuk referensi.
        jaw_width = dist(pt(2), pt(14))

        if jaw_width == 0: return 0, False

        # Rasio Utama: Seberapa lebar senyum dibanding muka?
        lip_jaw_ratio = lips_width / jaw_width

        # 3. Hitung Bukaan Mulut (Bibir Atas Bawah: 51 ke 57)
        mouth_opening = dist(pt(51), pt(57))
        
        # 4. Jarak Hidung ke Mulut (Hidung 33 ke Bibir Atas 51)
        nose_to_mouth = dist(pt(33), pt(51))
        
        if nose_to_mouth == 0: opening_ratio = 0
        else: opening_ratio = mouth_opening / nose_to_mouth

        # --- LOGIKA PENENTUAN SENYUM ---
        # Syarat 1: Bibir harus cukup lebar dibanding rahang
        is_wide_enough = lip_jaw_ratio > self.LIP_JAW_THRESHOLD
        
        # Syarat 2: (Opsional) Cek bukaan mulut agar tidak mendeteksi wajah datar yang lebar
        # Kita buat loose check: Asal rasio lebar bagus, kita anggap senyum.
        
        return lip_jaw_ratio, is_wide_enough

    def identify_user(self, frame_rgb, dlib_rect):
        """Identifikasi siapa orangnya (Login)"""
        if not self.memory_encodings: return "RED", None, 1.0
        
        # Konversi koordinat Dlib ke Face_Recognition (top, right, bottom, left)
        css_rect = (dlib_rect.top(), dlib_rect.right(), dlib_rect.bottom(), dlib_rect.left())
        
        try:
            # Encoding pakai library face_recognition (karena database kita formatnya ini)
            unknown_enc = face_recognition.face_encodings(frame_rgb, [css_rect])[0]
            
            dists = face_recognition.face_distance(self.memory_encodings, unknown_enc)
            idx = np.argmin(dists)
            min_dist = dists[idx]
            user = self.memory_users[idx]

            if min_dist < self.ZONE_GREEN: return "GREEN", user, min_dist
            elif min_dist < self.ZONE_YELLOW: return "YELLOW", user, min_dist
            else: return "RED", None, min_dist
        except:
            return "RED", None, 1.0
    
    def identify_face_zones(self, unknown_encoding):
        """Mencocokkan encoding wajah dengan database"""
        if not self.memory_encodings: return "RED", None, 1.0
        
        distances = face_recognition.face_distance(self.memory_encodings, unknown_encoding)
        best_match_idx = np.argmin(distances)
        min_dist = distances[best_match_idx]
        candidate = self.memory_users[best_match_idx]

        if min_dist < self.ZONE_GREEN: return "GREEN", candidate, min_dist
        elif min_dist < self.ZONE_YELLOW: return "YELLOW", candidate, min_dist
        else: return "RED", None, min_dist

    def process_frame(self, frame):
        self.frame_count += 1
        if self.frame_count % (self.SKIP_FRAMES + 1) != 0:
            return self.last_result

        h, w = frame.shape[:2]
        small_frame = cv2.resize(frame, (0, 0), fx=self.RESIZE_FACTOR, fy=self.RESIZE_FACTOR)
        gray = cv2.cvtColor(small_frame, cv2.COLOR_BGR2GRAY)
        
        # [FIX 2] Pastikan 'encoding' ada di dictionary default
        result = {
            "face_detected": False, "is_smiling": False, "smile_score": self.avg_ratio * 100,
            "zone": "RED", "user_data": None, "distance": 1.0, 
            "location": None, "encoding": None 
        }
        
        rects = self.detector(gray, 0)

        if len(rects) > 0:
            result["face_detected"] = True
            rect = max(rects, key=lambda r: r.width() * r.height())
            
            # Koordinat HD
            scale = 1 / self.RESIZE_FACTOR
            hd_rect = dlib.rectangle(
                int(rect.left() * scale), int(rect.top() * scale),
                int(rect.right() * scale), int(rect.bottom() * scale)
            )
            
            # Simpan lokasi
            result["location"] = (hd_rect.top(), hd_rect.right(), hd_rect.bottom(), hd_rect.left())

            # 1. ANALISIS SENYUM (HD)
            gray_hd = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            shape = self.predictor(gray_hd, hd_rect)
            raw_ratio, is_smiling = self.calculate_smile_hybrid(shape)
            
            # Skor & Stabilizer
            score = (raw_ratio - 0.40) * 1000 
            if score < 0: score = 0
            self.avg_ratio = (self.alpha * score) + ((1 - self.alpha) * self.avg_ratio)
            
            result["smile_score"] = self.avg_ratio
            result["is_smiling"] = is_smiling

            # 2. ENCODING & IDENTIFIKASI (Wajib utk Pendaftaran)
            # Konversi koordinat Dlib ke CSS (top, right, bottom, left)
            css_rect = (int(rect.top()), int(rect.right()), int(rect.bottom()), int(rect.left()))
            
            # Kita butuh RGB frame kecil untuk encoding (biar cepat)
            rgb_small = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
            
            try:
                # [FIX 3] Generate Encoding secara eksplisit
                encodings = face_recognition.face_encodings(rgb_small, [css_rect])
                
                if encodings:
                    unknown_encoding = encodings[0]
                    result["encoding"] = unknown_encoding # <--- INI YG KEMARIN HILANG!
                    
                    # Cek Database
                    zone, user, dist = self.identify_face_zones(unknown_encoding)
                    result["zone"] = zone
                    result["user_data"] = user
                    result["distance"] = dist
            except Exception as e:
                print(f"Encoding Error: {e}")

        else:
            self.avg_ratio = max(0, self.avg_ratio - 5.0)
            result["smile_score"] = self.avg_ratio

        self.last_result = result
        return result