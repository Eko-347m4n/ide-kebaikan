import cv2
import dlib
import numpy as np
import os
import json
import face_recognition # Tetap butuh ini utk encoding login awal
from core.logger import log # Import log

class VisionSystem:
    def __init__(self):
        
        base_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(base_dir, "shape_predictor_68_face_landmarks.dat")
        
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"❌ ERROR: File '{model_path}' hilang!")
        
        self.detector = dlib.get_frontal_face_detector()
        self.predictor = dlib.shape_predictor(model_path)

        self.memory_users = []
        self.memory_encodings = []
        
        # --- Thresholds ---
        self.ZONE_GREEN = 0.55  
        self.ZONE_YELLOW = 0.65
        self.SMILE_THRESHOLD = 0.40 
        self.MOUTH_AR_THRESHOLD = 0.5 # Mouth Aspect Ratio
        self.EYE_AR_THRESHOLD = 0.23 # Eye Aspect Ratio for blink

        # --- Frame Processing Settings ---
        self.frame_count = 0
        self.SKIP_FRAMES = 2 
        self.RESIZE_FACTOR = 0.50 
        
        # --- Smile Score Stabilizer ---
        self.avg_smile_score = 0.0
        self.smile_alpha = 0.3

        # --- Default Result Dictionary ---
        self.last_result = {
            "face_detected": False, 
            "is_smiling": False, 
            "is_mouth_open": False,
            "is_blinking": False,
            "smile_score": 0.0,
            "zone": "RED", 
            "user_data": None, 
            "distance": 1.0, 
            "location": None,
            "encoding": None
        }
        
    def load_memory(self, users_data):
        self.memory_users = []
        self.memory_encodings = []
        for user in users_data:
            if user['encoding']:
                try:
                    user_encodings_from_db = user["encoding"]

                    if isinstance(user_encodings_from_db[0], list): # If it's a list of lists (multiple encodings)
                        for enc in user_encodings_from_db:
                            self.memory_encodings.append(np.array(enc))
                            self.memory_users.append(user) # Append user for each encoding
                    else: # If it's a single list (old format or first encoding)
                        self.memory_encodings.append(np.array(user_encodings_from_db))
                        self.memory_users.append(user)
                except Exception as e: 
                    log.error(f"Error loading encoding for user {user.get('nama', 'Unknown')}, ID: {user.get('id', 'N/A')}. Error: {e}")

    # --- Geometric Expression Calculation ---

    def _get_eye_aspect_ratio(self, eye_landmarks):
        # vertical eye distances
        A = np.linalg.norm(eye_landmarks[1] - eye_landmarks[5])
        B = np.linalg.norm(eye_landmarks[2] - eye_landmarks[4])
        # horizontal eye distance
        C = np.linalg.norm(eye_landmarks[0] - eye_landmarks[3])
        # compute the eye aspect ratio
        ear = (A + B) / (2.0 * C)
        return ear

    def _get_mouth_aspect_ratio(self, mouth_landmarks):
        # vertical mouth distances
        A = np.linalg.norm(mouth_landmarks[1] - mouth_landmarks[7])
        B = np.linalg.norm(mouth_landmarks[2] - mouth_landmarks[6])
        C = np.linalg.norm(mouth_landmarks[3] - mouth_landmarks[5])
        # horizontal mouth distance
        D = np.linalg.norm(mouth_landmarks[0] - mouth_landmarks[4])
        # compute the mouth aspect ratio
        mar = (A + B + C) / (2.0 * D)
        return mar

    def _calculate_expressions(self, shape):
        # Helper to get (x, y) coordinates from dlib shape
        def get_coords(start, end):
            return np.array([(shape.part(i).x, shape.part(i).y) for i in range(start, end)])

        # 1. Smile Detection (Lip-Jaw Ratio)
        p = lambda n: np.array([shape.part(n).x, shape.part(n).y])
        lips_width = np.linalg.norm(p(48) - p(54))
        jaw_width = np.linalg.norm(p(2) - p(14))
        smile_ratio = lips_width / jaw_width if jaw_width > 0 else 0
        is_smiling = smile_ratio > self.SMILE_THRESHOLD

        # 2. Blink Detection (Eye Aspect Ratio)
        left_eye_pts = get_coords(36, 42)
        right_eye_pts = get_coords(42, 48)
        left_ear = self._get_eye_aspect_ratio(left_eye_pts)
        right_ear = self._get_eye_aspect_ratio(right_eye_pts)
        avg_ear = (left_ear + right_ear) / 2.0
        is_blinking = avg_ear < self.EYE_AR_THRESHOLD

        # 3. Mouth Open Detection (Mouth Aspect Ratio)
        inner_mouth_pts = get_coords(60, 68)
        mar = self._get_mouth_aspect_ratio(inner_mouth_pts)
        is_mouth_open = mar > self.MOUTH_AR_THRESHOLD

        return is_smiling, smile_ratio, is_blinking, is_mouth_open

    # --- Face Recognition ---

    def identify_face_zones(self, unknown_encoding):
        """Matches a face encoding against the database."""
        if not self.memory_encodings:
            log.info("VISION: memory_encodings is empty. Returning RED.")
            return "RED", None, 1.0
        
        distances = face_recognition.face_distance(self.memory_encodings, unknown_encoding)
        best_match_idx = np.argmin(distances)
        min_dist = distances[best_match_idx]
        candidate = self.memory_users[best_match_idx]

        log.info(f"VISION: Min_dist found: {min_dist:.4f} for user {candidate.get('nama', 'N/A')} ({candidate.get('kelas', 'N/A')})")
        log.info(f"VISION: ZONE_GREEN={self.ZONE_GREEN}, ZONE_YELLOW={self.ZONE_YELLOW}")

        if min_dist < self.ZONE_GREEN:
            log.info(f"VISION: Zone decision: GREEN for {candidate.get('nama', 'N/A')}")
            return "GREEN", candidate, min_dist
        elif min_dist < self.ZONE_YELLOW:
            log.info(f"VISION: Zone decision: YELLOW for {candidate.get('nama', 'N/A')}")
            return "YELLOW", candidate, min_dist
        else:
            log.info(f"VISION: Zone decision: RED (no strong match). Candidate: {candidate.get('nama', 'N/A')} dist: {min_dist:.4f}")
            return "RED", None, min_dist

    # --- Main Processing Function ---

    def process_frame(self, frame):
        self.frame_count += 1
        if self.frame_count % (self.SKIP_FRAMES + 1) != 0:
            return self.last_result

        # --- Pre-processing ---
        small_frame = cv2.resize(frame, (0, 0), fx=self.RESIZE_FACTOR, fy=self.RESIZE_FACTOR)
        gray = cv2.cvtColor(small_frame, cv2.COLOR_BGR2GRAY)
        
        # --- Result Initialization ---
        result = self.last_result.copy()
        result["face_detected"] = False # Reset detection for this frame

        # --- Face Detection ---
        rects = self.detector(gray, 0)

        if len(rects) > 0:
            result["face_detected"] = True
            rect = max(rects, key=lambda r: r.width() * r.height())
            
            # --- Landmark Prediction (on HD frame) ---
            scale = 1 / self.RESIZE_FACTOR
            hd_rect = dlib.rectangle(
                int(rect.left() * scale), int(rect.top() * scale),
                int(rect.right() * scale), int(rect.bottom() * scale)
            )
            gray_hd = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            shape = self.predictor(gray_hd, hd_rect)
            
            result["location"] = (hd_rect.top(), hd_rect.right(), hd_rect.bottom(), hd_rect.left())

            # --- Expression Analysis ---
            is_smiling, smile_ratio, is_blinking, is_mouth_open = self._calculate_expressions(shape)
            result["is_smiling"] = is_smiling
            result["is_blinking"] = is_blinking
            result["is_mouth_open"] = is_mouth_open

            # Smile Score stabilizer
            raw_smile_score = (smile_ratio - 0.40) * 1000 
            if raw_smile_score < 0: raw_smile_score = 0
            self.avg_smile_score = (self.smile_alpha * raw_smile_score) + ((1 - self.smile_alpha) * self.avg_smile_score)
            result["smile_score"] = self.avg_smile_score
            
            # --- Face Encoding and Identification (on small frame) ---
            css_rect = (int(rect.top()), int(rect.right()), int(rect.bottom()), int(rect.left()))
            rgb_small = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
            
            try:
                encodings = face_recognition.face_encodings(rgb_small, [css_rect])
                if encodings:
                    unknown_encoding = encodings[0]
                    result["encoding"] = unknown_encoding 
                    
                    zone, user, dist = self.identify_face_zones(unknown_encoding)
                    result["zone"] = zone
                    result["user_data"] = user
                    result["distance"] = dist
            except Exception as e:
                print(f"Encoding Error: {e}")
        
        else: # No face detected
            self.avg_smile_score = max(0, self.avg_smile_score - 5.0)
            result["smile_score"] = self.avg_smile_score

        self.last_result = result
        return result