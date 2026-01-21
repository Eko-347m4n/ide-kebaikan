import cv2
import time
import random
import threading
import queue
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
        self.last_activity_time = time.time()
        self.update_id = None
        
        # Threading & Queue
        self.frame_queue = queue.Queue(maxsize=2) # Keep queue small to ensure real-time feel
        self.stop_event = threading.Event()
        self.camera_thread = None

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

        if self.is_camera_on:
            return

        self.is_camera_on = True
        self.stop_event.clear()
        
        # Start Worker Thread
        self.camera_thread = threading.Thread(target=self._camera_worker, daemon=True)
        self.camera_thread.start()
        
        # Start UI Update Loop
        self._update_ui_loop()

    def go_to_sleep(self):
        log.info("💤 CameraManager: Going to Sleep...")
        self.is_camera_on = False
        
        # Signal thread to stop
        self.stop_event.set()
        
        # Clear queue to prevent processing stale frames
        with self.frame_queue.mutex:
            self.frame_queue.queue.clear()

        # Wait for thread to finish (optional, but good for cleanup)
        if self.camera_thread and self.camera_thread.is_alive():
            self.camera_thread.join(timeout=1.0)
            
        if self.update_id:
            self.master_app.after_cancel(self.update_id)
            self.update_id = None
        
        # Reset all logic state
        self._reset_logic_state()
        self.challenge_update_callback(None)

    def _reset_logic_state(self):
        self.current_challenge = None
        self.challenge_start_time = None
        self.identified_user_data = None
        self.identified_encoding = None
        self.identified_zone = None
        self.identified_min_dist = None
        self.identity_established_time = None
        self.unrecognized_face_start_time = None

    def _camera_worker(self):
        """Worker thread: Handles OpenCV capture and Vision Processing."""
        log.info("📷 Camera Thread: Started.")
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            log.error("📷 Camera Thread: Failed to open camera.")
            self.frame_queue.put("ERROR")
            return

        while not self.stop_event.is_set():
            ret, frame = cap.read()
            if not ret:
                self.frame_queue.put("ERROR")
                break
            
            # Flip logic
            frame = cv2.flip(frame, 1)
            
            # Heavy processing (Vision)
            vision_data = self.vision.process_frame(frame)
            
            # Put to queue (drop old frame if queue is full)
            if self.frame_queue.full():
                try:
                    self.frame_queue.get_nowait()
                except queue.Empty:
                    pass
            
            self.frame_queue.put((frame, vision_data))
            
            # Small sleep to prevent 100% CPU usage on this thread if camera is fast
            time.sleep(0.01) 
            
        cap.release()
        log.info("📷 Camera Thread: Stopped.")

    def _update_ui_loop(self):
        """Main Thread: Consumes queue and updates UI."""
        if not self.is_camera_on:
            return

        # Auto-sleep check
        if time.time() - self.last_activity_time > SLEEP_TIMEOUT:
            log.info("💤 CameraManager: Auto Sleep Activated!")
            self.go_to_sleep()
            return

        try:
            # Non-blocking get
            data = self.frame_queue.get_nowait()
            
            if data == "ERROR":
                self.display_frame_callback(None, CAM_ERROR)
            else:
                frame, vision_data = data
                self._process_game_logic(frame, vision_data)

        except queue.Empty:
            pass # No new frame, skip

        if self.is_camera_on:
            self.update_id = self.master_app.after(10, self._update_ui_loop)

    def _process_game_logic(self, frame, data):
        """Processes logic using the latest frame and vision data, then updates UI."""
        
        # 1. DRAWING BOUNDING BOXES
        if data["face_detected"] and data["location"]:
            top, right, bottom, left = data["location"]
            display_zone = self.identified_zone if self.identified_user_data else data["zone"]
            
            color = FACE_BOX_RED
            if display_zone == "GREEN": color = FACE_BOX_GREEN
            elif display_zone == "YELLOW": color = FACE_BOX_YELLOW
            cv2.rectangle(frame, (left, top), (right, bottom), color, 3)
        
        # 2. LOGIC HANDLING
        if data["face_detected"]:
            self.last_activity_time = time.time() # Reset sleep timer

            # Case A: Belum teridentifikasi stabil (Masih mencari/validasi identitas)
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
            
            # Case B: Identitas sudah stabil, lanjut ke Challenge (Liveness)
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

                    # Draw Progress Bar
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
                        self._reset_logic_state() # Reset for next time
                        self.challenge_update_callback(None)
                        return
                else:
                    self.challenge_start_time = None

        else: # No face detected
            if self.identified_user_data is not None or self.current_challenge is not None or self.unrecognized_face_start_time is not None:
                log.info("Face lost, resetting identity and challenge state.")
                self._reset_logic_state()
                self.challenge_update_callback(CAM_STARTING)

        # 3. DISPLAY FINAL IMAGE
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame_rgb)
        img_tk = ctk.CTkImage(light_image=img, dark_image=img, size=(640, 480))
        self.display_frame_callback(img_tk)

    def shutdown(self):
        """Releases camera resources and stops the update loop."""
        self.go_to_sleep()
