import cv2
import time
import random
import customtkinter as ctk
from PIL import Image
from core.vision import VisionSystem
from core.logger import log
from core.constants import (
    SLEEP_TIMEOUT, SMILE_HOLD_DURATION, UNRECOGNIZED_FACE_HOLD_DURATION, CAM_STARTING, CAM_ERROR,
    FACE_BOX_RED, FACE_BOX_GREEN, FACE_BOX_YELLOW,
    SMILE_PROGRESS_BAR_COLOR, SMILE_PROGRESS_TEXT_COLOR
)

class CameraManager:
    def __init__(self, master_app, vision_system, display_frame_callback, login_trigger_callback, challenge_update_callback):
        self.master_app = master_app
        self.vision = vision_system
        self.display_frame_callback = display_frame_callback
        self.login_trigger_callback = login_trigger_callback 
        self.challenge_update_callback = challenge_update_callback

        self.is_camera_on = False
        self.cap = None
        self.last_activity_time = time.time()
        self.update_id = None

        # --- Liveness Detection State ---
        self.challenges = ["smile", "mouth_open", "blink"]
        self.current_challenge = None
        self.challenge_start_time = None
        self.challenge_text_map = {
            "smile": "Tahan Senyum! 😊",
            "mouth_open": "Buka Mulut! 😮",
            "blink": "Kedipkan Mata! 😉"
        }
        self.IDENTITY_HOLD_DURATION = 0.5 # Wajah harus stabil selama ini sebelum tantangan

        # --- Identity First State ---
        self.identified_user_data = None
        self.identified_encoding = None
        self.identified_zone = None
        self.identified_min_dist = None
        self.identity_established_time = None
        self.unrecognized_face_start_time = None

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
                self.display_frame_callback(None, CAM_ERROR)
                return
        
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
        
        # Reset all liveness and identity state on sleep
        self.current_challenge = None
        self.challenge_start_time = None
        self.identified_user_data = None
        self.identified_encoding = None
        self.identified_zone = None
        self.identified_min_dist = None
        self.identity_established_time = None
        self.unrecognized_face_start_time = None
        self.challenge_update_callback(None)

    def _update_camera(self):
        if not self.is_camera_on:
            return

        # Auto-sleep check
        if time.time() - self.last_activity_time > SLEEP_TIMEOUT:
            log.info("💤 CameraManager: Auto Sleep Activated!")
            self.go_to_sleep()
            return

        ret, frame = self.cap.read()
        if ret:
            frame = cv2.flip(frame, 1)
            data = self.vision.process_frame(frame)
            
            if data["face_detected"] and data["location"]:
                top, right, bottom, left = data["location"]
                display_zone = self.identified_zone if self.identified_user_data else data["zone"]
                
                color = FACE_BOX_RED
                if display_zone == "GREEN": color = FACE_BOX_GREEN
                elif display_zone == "YELLOW": color = FACE_BOX_YELLOW
                cv2.rectangle(frame, (left, top), (right, bottom), color, 3)
            
            if data["face_detected"]:
                self.last_activity_time = time.time()

                if self.identified_user_data is None:
                    if data["zone"] == "GREEN" or data["zone"] == "YELLOW":
                        self.unrecognized_face_start_time = None
                        if self.identity_established_time is None:
                            self.identity_established_time = time.time()
                            self.challenge_update_callback(f"ID Ditemukan: {data['user_data']['nama']}! Tahan posisi...")
                        
                        elif time.time() - self.identity_established_time > self.IDENTITY_HOLD_DURATION:
                            self.identified_user_data = data["user_data"]
                            self.identified_encoding = data["encoding"]
                            self.identified_zone = data["zone"]
                            self.identified_min_dist = data["distance"]
                            log.info(f"Identity established: {self.identified_user_data['nama']} (Zone: {self.identified_zone}, Dist: {self.identified_min_dist:.4f})")
                            self.challenge_update_callback("ID Stabil. Siap Tantangan!")
                            self.identity_established_time = None
                    elif data["zone"] == "RED":
                        self.identity_established_time = None
                        if self.unrecognized_face_start_time is None:
                            self.unrecognized_face_start_time = time.time()
                            self.challenge_update_callback("Wajah baru terdeteksi. Tahan posisi untuk daftar...")
                        elif time.time() - self.unrecognized_face_start_time > UNRECOGNIZED_FACE_HOLD_DURATION:
                            data_for_app = {
                                "zone": "RED",
                                "user_data": None,
                                "encoding": data["encoding"],
                                "distance": None,
                                "face_detected": True,
                                "location": data["location"]
                            }
                            self.login_trigger_callback(data_for_app)
                            self.unrecognized_face_start_time = None
                            return
                    else:
                        self.identity_established_time = None
                        self.unrecognized_face_start_time = None
                        self.challenge_update_callback(CAM_STARTING)
                
                elif self.identified_user_data is not None and self.identified_zone is not None:
                    if self.current_challenge is None:
                        self.current_challenge = random.choice(self.challenges)
                        self.challenge_update_callback(self.challenge_text_map[self.current_challenge])
                        self.challenge_start_time = None
                    
                    liveness_detected = False
                    if self.current_challenge == "smile":
                        liveness_detected = data["is_smiling"]
                    elif self.current_challenge == "mouth_open":
                        liveness_detected = data["is_mouth_open"]
                    elif self.current_challenge == "blink":
                        liveness_detected = data["is_blinking"]

                    if liveness_detected:
                        if self.challenge_start_time is None:
                            self.challenge_start_time = time.time()
                        
                        elapsed = time.time() - self.challenge_start_time
                        progress = min(elapsed / SMILE_HOLD_DURATION, 1.0)

                        top, right, bottom, left = data["location"]
                        bar_w = 200
                        bx, by = left + (right - left) // 2 - bar_w // 2, top - 30
                        cv2.rectangle(frame, (bx, by), (bx + bar_w, by + 10), (200, 200, 200), -1)
                        fill_w = int(bar_w * progress)
                        cv2.rectangle(frame, (bx, by), (bx + fill_w, by + 10), SMILE_PROGRESS_BAR_COLOR, -1)
                        
                        if elapsed >= SMILE_HOLD_DURATION:
                            data_for_app = {
                                "zone": self.identified_zone,
                                "user_data": self.identified_user_data,
                                "encoding": self.identified_encoding,
                                "distance": self.identified_min_dist,
                                "face_detected": True,
                                "location": data["location"]
                            }
                            self.login_trigger_callback(data_for_app)
                            
                            self.current_challenge = None
                            self.challenge_start_time = None
                            self.identified_user_data = None
                            self.identified_encoding = None
                            self.identified_zone = None
                            self.identified_min_dist = None
                            self.identity_established_time = None
                            self.unrecognized_face_start_time = None
                            self.challenge_update_callback(None)
                            return
                    else:
                        self.challenge_start_time = None

            else: # No face detected
                if self.identified_user_data is not None or self.current_challenge is not None or self.unrecognized_face_start_time is not None:
                    log.info("Face lost, resetting identity and challenge state.")
                    self.identified_user_data = None
                    self.identified_encoding = None
                    self.identified_zone = None
                    self.identified_min_dist = None
                    self.identity_established_time = None
                    self.current_challenge = None
                    self.challenge_start_time = None
                    self.unrecognized_face_start_time = None
                    self.challenge_update_callback(CAM_STARTING)

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            img_tk = ctk.CTkImage(light_image=img, dark_image=img, size=(640, 480))
            self.display_frame_callback(img_tk)

        else: # No frame from camera
            self.display_frame_callback(None, CAM_ERROR)

        if self.is_camera_on:
            self.update_id = self.master_app.after(10, self._update_camera)

    def shutdown(self):
        """Releases camera resources and stops the update loop."""
        self.go_to_sleep()
