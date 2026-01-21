import cv2
import dlib
import numpy as np
import os
import json
import face_recognition # Tetap butuh ini utk encoding login awal
from sklearn.neighbors import KDTree # Optimalisasi pencarian wajah
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
        self.face_tree = None # KDTree index
        
        # --- Thresholds ---
        self.ZONE_GREEN = 0.48  # Diperketat dari 0.55 (Standar face_recognition 0.6 itu longgar)
        self.ZONE_YELLOW = 0.60
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

        # --- Identity Stabilization (Optimization) ---
        self.last_face_center = None
        self.frames_since_identity_check = 0
        self.IDENTITY_CHECK_INTERVAL = 15 # Re-check identity every 15 processed frames if stable

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
        
        # Build KDTree Index
        if self.memory_encodings:
            try:
                log.info(f"🌳 Building KDTree for {len(self.memory_encodings)} face encodings...")
                self.face_tree = KDTree(self.memory_encodings, metric='euclidean')
            except Exception as e:
                log.error(f"Failed to build KDTree: {e}")
                self.face_tree = None
        else:
            self.face_tree = None

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
        """Matches a face encoding using Fast KDTree Search."""
        if self.face_tree is None or not self.memory_encodings:
            return "RED", None, 1.0
        
        # Query KDTree for nearest neighbors
        # k=2 to allow ambiguity check (compare best match vs runner-up)
        k_neighbors = min(len(self.memory_users), 2)
        
        # reshape(1, -1) because query expects 2D array
        dists, indices = self.face_tree.query([unknown_encoding], k=k_neighbors)
        
        min_dist = dists[0][0]
        best_match_idx = indices[0][0]
        candidate = self.memory_users[best_match_idx]
        
        # --- AMBIGUITY CHECK ---
        # If we found at least 2 neighbors
        if k_neighbors > 1:
            second_dist = dists[0][1]
            second_idx = indices[0][1]
            candidate_2 = self.memory_users[second_idx]
            
            # If the gap between #1 and #2 is very small (< 0.05) AND they are different people
            if (second_dist - min_dist < 0.05) and (candidate['id'] != candidate_2['id']):
                log.warning(f"VISION: Ambiguous match! {candidate['nama']} ({min_dist:.3f}) vs {candidate_2['nama']} ({second_dist:.3f}). Rejecting.")
                return "RED", None, min_dist

        log.info(f"VISION: Min_dist found: {min_dist:.4f} for user {candidate.get('nama', 'N/A')}")

        if min_dist < self.ZONE_GREEN:
            return "GREEN", candidate, min_dist
        elif min_dist < self.ZONE_YELLOW:
            return "YELLOW", candidate, min_dist
        else:
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
            
            # --- Optimization: Check if we need to re-encode (Identity Locking) ---
            current_center = np.array([(rect.left() + rect.right()) // 2, (rect.top() + rect.bottom()) // 2])
            should_encode = True
            
            if self.last_result["user_data"] is not None and self.last_face_center is not None:
                # Calculate movement distance (in small frame pixels)
                dist = np.linalg.norm(current_center - self.last_face_center)
                
                # If stable (moved < 20px) and checked recently, skip encoding
                if dist < 20 and self.frames_since_identity_check < self.IDENTITY_CHECK_INTERVAL:
                    should_encode = False
                    self.frames_since_identity_check += 1
                else:
                    self.frames_since_identity_check = 0 # Reset if moved or time up
            
            self.last_face_center = current_center

            if should_encode:
                # --- Face Encoding and Identification (Heavy) ---
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
            else:
                # Reuse previous identity
                result["zone"] = self.last_result["zone"]
                result["user_data"] = self.last_result["user_data"]
                result["distance"] = self.last_result["distance"]
                result["encoding"] = self.last_result["encoding"]
        
        else: # No face detected
            self.avg_smile_score = max(0, self.avg_smile_score - 5.0)
            result["smile_score"] = self.avg_smile_score
            self.last_face_center = None # Reset tracker
            self.frames_since_identity_check = 0

        self.last_result = result
        return result