from enum import Enum, auto

class AppState(Enum):
    CAMERA = auto()
    CONFIRM = auto()
    REGISTER = auto()
    INPUT = auto()
    LOADING = auto()
    RESULT = auto()
    STANDBY = auto()

# --- Timeouts (in seconds) ---
SLEEP_TIMEOUT = 300 
SMILE_HOLD_DURATION = 2.5
UNRECOGNIZED_FACE_HOLD_DURATION = 2.0
AUTO_RESET_AFTER_SUCCESS = 7.0

# --- UI Texts ---
# General
APP_TITLE = "Berburu Kebaikan"
SIDEBAR_TITLE = "✨ BERBURU IDE KEBAIKAN ✨"

# Camera Page
CAM_INFO_SLEEP = "Sistem Sedang Tidur 💤"
CAM_INFO_WAKE_UP = "Senyum untuk Login 😊"
CAM_CLICK_TO_START = "Klik Layar untuk Mulai 🚀"
CAM_ERROR = "Kamera Error / Loading... ⏳"
CAM_STARTING = "Menyalakan Kamera... 📷"

# Result Page
RESULT_TITLE = "✨ HASIL ANALISIS ✨"
RESULT_SUCCESS_ICON_HIGH = "🏆"
RESULT_SUCCESS_ICON_LOW = "⭐"
RESULT_FAILURE_ICON = "🚫"

# --- UI Colors & Styles ---
COLOR_BACKGROUND = "#F0F0F0"
COLOR_CONF_BG = "#F0F0F0"
COLOR_SUCCESS_BORDER = "#FFD700"
COLOR_SCORE = "#FFA500"
COLOR_FAILURE_BORDER = "red"

# --- Leaderboard ---
LEADERBOARD_LIMIT = 10

# --- Camera Processing ---
ZONE_GREEN = "GREEN"
ZONE_YELLOW = "YELLOW"
ZONE_RED = "RED"

SMILE_PROGRESS_BAR_COLOR = (0, 255, 0)
SMILE_PROGRESS_TEXT_COLOR = (0, 255, 0)
FACE_BOX_GREEN = (0, 255, 0)
FACE_BOX_YELLOW = (0, 255, 255)
FACE_BOX_RED = (0, 0, 255)
