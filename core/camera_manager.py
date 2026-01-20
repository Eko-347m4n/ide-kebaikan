import cv2
import time
import customtkinter as ctk
from PIL import Image
from core.vision import VisionSystem
from core.logger import log
from core.constants import (
    SLEEP_TIMEOUT, SMILE_HOLD_DURATION, CAM_STARTING, CAM_ERROR,
    FACE_BOX_RED, FACE_BOX_GREEN, FACE_BOX_YELLOW,
    SMILE_PROGRESS_BAR_COLOR, SMILE_PROGRESS_TEXT_COLOR,
    ZONE_GREEN, ZONE_YELLOW
)

class CameraManager:
    def __init__(self, master_app, vision_system, display_frame_callback, login_trigger_callback):
        self.master_app = master_app # For after calls
        self.vision = vision_system
        self.display_frame_callback = display_frame_callback
        self.login_trigger_callback = login_trigger_callback

        self.is_camera_on = False
        self.cap = None
        self.last_activity_time = time.time()
        self.smile_start_time = None
        self.update_id = None # To store after() job id

    def wake_up_system(self):
        log.info("🚀 CameraManager: Waking Up System...")
        self.last_activity_time = time.time()

        if self.is_camera_on and self.cap is not None and self.cap.isOpened():
            return

        self.is_camera_on = True
        if self.cap is None or not self.cap.isOpened():
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                log.error("Failed to open camera.")
                self.is_camera_on = False
                # Optionally, you might want to call display_frame_callback with an error message here
                self.display_frame_callback(None, CAM_ERROR)
                return
        
        # Initial call to start the camera loop
        self._update_camera()

    def go_to_sleep(self):
        log.info("💤 CameraManager: Going to Sleep...")
        self.is_camera_on = False
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        if self.update_id:
            self.master_app.after_cancel(self.update_id)
            self.update_id = None
        self.smile_start_time = None # Reset smile detection on sleep

    def _update_camera(self):
        if not self.is_camera_on:
            return

        elapsed_idle = time.time() - self.last_activity_time
        if elapsed_idle > SLEEP_TIMEOUT:
            log.info("💤 CameraManager: Auto Sleep Activated!")
            self.go_to_sleep()
            return

        ret, frame = self.cap.read()
        if ret:
            frame = cv2.flip(frame, 1)
            data = self.vision.process_frame(frame)
            
            if data["face_detected"]:
                self.last_activity_time = time.time()

            if data["face_detected"] and data["location"]:
                top, right, bottom, left = data["location"]
                zone = data["zone"]
                
                color = FACE_BOX_RED
                if zone == ZONE_GREEN: color = FACE_BOX_GREEN
                elif zone == ZONE_YELLOW: color = FACE_BOX_YELLOW
                
                cv2.rectangle(frame, (left, top), (right, bottom), color, 3)

                if data["is_smiling"]:
                    if self.smile_start_time is None:
                        self.smile_start_time = time.time() 
                    
                    elapsed = time.time() - self.smile_start_time
                    progress = min(elapsed / SMILE_HOLD_DURATION, 1.0)

                    bar_w = 200
                    bx, by = left + (right-left)//2 - bar_w//2, top - 30
                    cv2.rectangle(frame, (bx, by), (bx + bar_w, by + 10), (200, 200, 200), -1)
                    fill_w = int(bar_w * progress)
                    cv2.rectangle(frame, (bx, by), (bx + fill_w, by + 10), SMILE_PROGRESS_BAR_COLOR, -1)
                    cv2.putText(frame, "TAHAN SENYUMNYAA...", (bx, by-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, SMILE_PROGRESS_TEXT_COLOR, 1)

                    if elapsed >= SMILE_HOLD_DURATION:
                        self.smile_start_time = None 
                        self.login_trigger_callback(data) 
                        return # Exit to avoid displaying frame/looping until next trigger
                else:
                    self.smile_start_time = None

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            img_tk = ctk.CTkImage(light_image=img, dark_image=img, size=(640, 480))
            self.display_frame_callback(img_tk)

        else:
            self.display_frame_callback(None, CAM_ERROR) # Signal error/loading to UI

        if self.is_camera_on:
            self.update_id = self.master_app.after(10, self._update_camera)

    def shutdown(self):
        """Releases camera resources and stops the update loop."""
        self.go_to_sleep()
