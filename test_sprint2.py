import cv2
import time
from core.brain import BrainLogic
from core.vision import VisionSystem

print("🚀 TEST SPRINT 2 (LITE MODE REVERTED)...")
brain = BrainLogic()
vision = VisionSystem()

# Load Data
users = brain.get_all_users()
vision.load_memory(users)

cap = cv2.VideoCapture(0)
print("📸 Kamera terbuka. Harusnya ringan sekarang.")

while True:
    ret, frame = cap.read()
    if not ret: break
    
    frame = cv2.flip(frame, 1)
    
    # Proses (Direct Call, No Threading)
    data = vision.process_frame(frame)
    
    if data["face_detected"] and data["location"]:
        top, right, bottom, left = data["location"]
        zone = data["zone"]
        score = data["smile_score"]
        smiling = data["is_smiling"]
        
        # Warna
        color = (0, 0, 255) # Merah
        if zone == "GREEN": color = (0, 255, 0)
        elif zone == "YELLOW": color = (0, 255, 255)

        cv2.rectangle(frame, (left, top), (right, bottom), color, 3)
        
        # Info Senyum
        # Jika skor 0, bar kosong. Jika >0 baru muncul.
        status = "SENYUM!" if smiling else "Netral"
        bar_len = int(score * 2) 
        cv2.rectangle(frame, (left, bottom+10), (left+bar_len, bottom+20), (0, 255, 0), -1)
        
        text = f"Score: {score:.0f} | {status}"
        cv2.putText(frame, text, (left, bottom+40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    cv2.imshow('TEST LITE', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()