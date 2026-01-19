import os

# Base Directory (Project Root)
# Karena file ini ada di folder 'core', kita naik satu level untuk dapat root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class Config:
    # --- PATHS ---
    DATA_DIR = os.path.join(BASE_DIR, 'data')
    CORE_DIR = os.path.join(BASE_DIR, 'core')

    DB_PATH = os.path.join(DATA_DIR, 'kebaikan.db')
    TRAINING_DATA_PATH = os.path.join(DATA_DIR, 'training_data.csv')
    LEARNED_DATA_PATH = os.path.join(DATA_DIR, 'learned_data.csv')
    
    MODEL_PATH = os.path.join(CORE_DIR, 'trained_brain.pkl')
    DLIB_MODEL_PATH = os.path.join(CORE_DIR, 'shape_predictor_68_face_landmarks.dat')

    # --- VISION SYSTEM ---
    CAMERA_INDEX = 0      # 0 untuk webcam default
    RESIZE_FACTOR = 0.25  # Ukuran frame untuk processing (makin kecil makin cepat)
    SKIP_FRAMES = 3       # Proses 1 frame setiap n frame (hemat CPU)

    # Recognition Thresholds (Makin kecil makin ketat)
    ZONE_GREEN = 0.45     # Batas kemiripan wajah (Pasti Kenal)
    ZONE_YELLOW = 0.65    # Batas kemiripan wajah (Mungkin Kenal)

    # Smile Logic
    LIP_JAW_THRESHOLD = 0.50
    OPENING_THRESHOLD = 0.30
    SMILE_HOLD_DURATION = 3.0 # Detik harus senyum

    # --- APP / UI ---
    APP_TITLE = "Berburu Kebaikan"
    APP_GEOMETRY = "1100x700"
    
    # Timeouts (in seconds or ms)
    SLEEP_TIMEOUT = 300       # 5 Menit idle -> Sleep
    AUTO_CLOSE_DELAY = 4000   # 4 Detik delay setelah result sebelum reset
    ANIMATION_SPEED = 20      # ms untuk animasi confetti
