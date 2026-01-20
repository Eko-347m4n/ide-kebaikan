import customtkinter as ctk
import time
import threading
from core.brain import BrainLogic
from core.vision import VisionSystem
from core.logger import log
from core.constants import (
    AppState, AUTO_RESET_AFTER_SUCCESS, APP_TITLE, SIDEBAR_TITLE,
    CAM_INFO_SLEEP, CAM_INFO_WAKE_UP, CAM_CLICK_TO_START, CAM_STARTING,
    LEADERBOARD_LIMIT, ZONE_GREEN, ZONE_YELLOW
)
from ui.camera_page import CameraPage
from ui.confirm_page import ConfirmPage
from ui.input_page import InputPage
from ui.loading_page import LoadingPage
from ui.register_page import RegisterPage
from ui.result_page import ResultPage
from core.camera_manager import CameraManager

class GoodDeedApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- Window and Grid Setup ---
        self.title(APP_TITLE)
        self.geometry("1000x600")
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- System Components ---
        self.brain = BrainLogic()
        self.vision = VisionSystem()
        
        # --- State Management ---
        self.current_state = AppState.STANDBY
        self.active_user = None
        self.pending_encoding = None
        self.auto_reset_timer = None
        self.temp_potential_user = None

        # --- UI and Services ---
        self._setup_sidebar()
        self._setup_main_area()
        
        self.camera_manager = CameraManager(
            master_app=self,
            vision_system=self.vision,
            display_frame_callback=self._display_camera_frame,
            login_trigger_callback=self._handle_login_trigger
        )
        
        # --- Initial State ---
        self.vision.load_memory(self.brain.get_all_users())
        
        if not self.brain.is_trained:
            self._train_model_flow()
        else:
            self._go_to_sleep()

    def _train_model_flow(self):
        """Shows a training screen and runs the model training in a thread."""
        self._show_frame(AppState.LOADING)
        self.loading_page.set_text("Model AI sedang disiapkan... (± 15 detik)")
        
        def run_training():
            self.brain.train()
            # Once training is done, schedule the next step in the main thread
            self.after(100, self._on_training_complete)
            
        # Run training in a separate thread to not freeze the GUI
        training_thread = threading.Thread(target=run_training)
        training_thread = threading.Thread(target=self._run_training_in_thread)
        training_thread.daemon = True
        training_thread.start()
    
    def _run_training_in_thread(self):                                                                              
     """The actual training process, run in a background thread."""                                              
     self.brain.train()                                                                                          
     # Once training is done, schedule the next step in the main thread                                          
     self.after(100, self._on_training_complete)

    def _on_training_complete(self):
        """Callback executed in the main thread after the model is trained."""
        log.info("Model training complete.")
        self._go_to_sleep()
        self._show_frame(AppState.CAMERA)

    def _setup_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(4, weight=1)

        logo_label = ctk.CTkLabel(self.sidebar, text=SIDEBAR_TITLE, font=ctk.CTkFont(size=24, weight="bold"))
        logo_label.grid(row=0, column=0, padx=20, pady=(30, 10))

        status_container = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        status_container.grid(row=1, column=0, padx=20, pady=10)

        self.status_dot = ctk.CTkLabel(status_container, text="●", font=ctk.CTkFont(size=24), text_color="red")
        self.status_dot.pack(side="left", padx=5)
        
        self.status_text = ctk.CTkLabel(status_container, text="OFFLINE", font=ctk.CTkFont(weight="bold"))
        self.status_text.pack(side="left")

        ctk.CTkLabel(self.sidebar, text="_________________________").grid(row=2, column=0, pady=10)

        lb_title = ctk.CTkLabel(self.sidebar, text="🏆 Top Siswa", font=ctk.CTkFont(size=18, weight="bold"))
        lb_title.grid(row=3, column=0, padx=20, pady=(10, 10))

        self.leaderboard_frame = ctk.CTkScrollableFrame(self.sidebar, label_text="Minggu Ini", fg_color="white")
        self.leaderboard_frame.grid(row=4, column=0, padx=20, pady=10, sticky="nsew")
        self.update_leaderboard()

    def _setup_main_area(self):
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

        # Instantiate all pages
        self.camera_page = CameraPage(main_frame, wake_up_callback=self._wake_up_system)
        self.confirm_page = ConfirmPage(main_frame, yes_callback=self._on_confirm_yes, no_callback=self._on_confirm_no)
        self.register_page = RegisterPage(main_frame, submit_callback=self._submit_registration, cancel_callback=self.start_reset)
        self.input_page = InputPage(main_frame, submit_callback=self._submit_idea, cancel_callback=self.start_reset)
        self.loading_page = LoadingPage(main_frame)
        self.result_page = ResultPage(main_frame, reset_callback=self.start_reset)
        
        self._show_frame(AppState.CAMERA)
    
    
    def update_leaderboard(self):
        for widget in self.leaderboard_frame.winfo_children():
            widget.destroy()
            
        data = self.brain.get_leaderboard(LEADERBOARD_LIMIT)
        if not data:
            ctk.CTkLabel(self.leaderboard_frame, text="Belum ada data.").pack()
            return
            
        for idx, (name, class_name, score) in enumerate(data):
            row = ctk.CTkFrame(self.leaderboard_frame, fg_color="transparent")
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=f"{idx+1}. {name} ({class_name})", anchor="w").pack(side="left", padx=5)
            ctk.CTkLabel(row, text=f"{score} Pts", font=ctk.CTkFont(weight="bold")).pack(side="right", padx=5)

    def start_reset(self):
        self.loading_page.set_text("Sabar ya, sedang proses menuju ke halaman awal... 🔄")
        self._show_frame(AppState.LOADING)
        self.after(2000, self._reset_app)

    def _reset_app(self):
        self._go_to_sleep()
        self._cancel_auto_reset_timer()
        
        self.register_page.reset()
        self.input_page.reset()
        self.active_user = None
        self.pending_encoding = None
        
        try:
            self.camera_page.clear_cam_image()
            self.camera_page.set_cam_text(CAM_STARTING)
        except Exception as e:
            log.error(f"Error resetting camera page UI: {e}")

        self.after(300, self._wake_up_system)


    def _show_frame(self, state):
        pages = {
            AppState.CAMERA: self.camera_page,
            AppState.CONFIRM: self.confirm_page,
            AppState.REGISTER: self.register_page,
            AppState.INPUT: self.input_page,
            AppState.LOADING: self.loading_page,
            AppState.RESULT: self.result_page,
        }
        
        for page in pages.values():
            page.pack_forget()

        if state != AppState.CAMERA:
            self.camera_manager.go_to_sleep()
            try:
                self.camera_page.clear_cam_image() # Ensure UI is visually cleared
            except Exception as e:
                 log.error(f"Error clearing camera image: {e}")

        page_to_show = pages.get(state)
        self.current_state = state

        if page_to_show:
            pack_options = {"fill": "both", "expand": True}
            if state not in [AppState.CAMERA]:
                 pack_options.update({"padx": 50, "pady": 50})
            page_to_show.pack(**pack_options)

        # Post-show actions
        if state == AppState.INPUT:
            self.input_page.reset()
            self.input_page.focus_textbox()

    def _display_camera_frame(self, img_tk, text_message=None):
        try:
            if img_tk:
                self.camera_page.set_cam_image(img_tk)
            elif text_message:
                self.camera_page.set_cam_text(text_message)
        except Exception as e:
            log.error(f"Error displaying camera frame: {e}")

    # --- SYSTEM & CAMERA CONTROL ---

    def _wake_up_system(self, event=None):
        log.info("🚀 GoodDeedApp: Waking Up System...")
        self.camera_manager.wake_up_system()

        self.status_dot.configure(text_color="green")
        self.status_text.configure(text="ONLINE", text_color="green")
        
        try:
            self.camera_page.set_info_text(CAM_INFO_WAKE_UP, color="blue")
        except Exception as e:
            log.error(f"Error setting wake up text: {e}")
            
        self._show_frame(AppState.CAMERA)
            
    def _go_to_sleep(self):
        log.info("💤 GoodDeedApp: System Going to Sleep...")
        self.camera_manager.go_to_sleep()
        
        self.status_dot.configure(text_color="red")
        self.status_text.configure(text="OFFLINE", text_color="red")
        
        try:
            self.camera_page.set_info_text(CAM_INFO_SLEEP, color="gray")
            self.camera_page.clear_cam_image()
            self.camera_page.set_cam_text(CAM_CLICK_TO_START, color="gray")
        except Exception as e:
            log.error(f"Error setting sleep UI: {e}")

    def _handle_login_trigger(self, vision_data):
        """Handles the event when a user is identified by the camera."""
        zone = vision_data["zone"]
        user = vision_data["user_data"]
        
        self.pending_encoding = vision_data["encoding"]
        self.temp_potential_user = user 
        
        if zone == ZONE_GREEN:
            self.active_user = user
            self.input_page.set_welcome_message(user['nama'])
            self._show_frame(AppState.INPUT)
        elif zone == ZONE_YELLOW:
            self.confirm_page.set_name(user['nama'])
            self._show_frame(AppState.CONFIRM)
        else: # RED
            self._show_frame(AppState.REGISTER)
            
    def _on_confirm_yes(self):
        self.active_user = self.temp_potential_user
        self.input_page.set_welcome_message(self.active_user['nama'])
        self._show_frame(AppState.INPUT)

    def _on_confirm_no(self):
        self._show_frame(AppState.REGISTER)

    def _submit_registration(self):
        user_data = self.register_page.get_values()
        name = user_data["nama"]
        class_name = user_data["kelas"]

        if not name or not class_name:
            log.warning("Registration submission with empty name or class.")
            return
            
        if self.pending_encoding is not None:
            success, msg = self.brain.register_user(name, class_name, self.pending_encoding)
            if success:
                self.vision.load_memory(self.brain.get_all_users())
                self.active_user = {"nama": name, "kelas": class_name}
                self.input_page.set_welcome_message(name)
                self._show_frame(AppState.INPUT)
            else:
                log.error(f"Failed to register user: {msg}")

    def _submit_idea(self):
        """Handles the submission of a user's good idea."""
        text = self.input_page.get_idea_text()
        if len(text) < 5:
            log.warning("Idea submission too short.")
            return

        self._show_frame(AppState.LOADING)
        self.after(100, lambda: self._process_idea_submission(text))

    def _process_idea_submission(self, text):
        result = self.brain.predict_and_score(text)

        self.loading_page.set_text("Menganalisis kadar kebaikanmu nih 🧐")
        self.after(1000, lambda: self.loading_page.set_text("Menghitung poin..."))
        self.after(2000, lambda: self._display_submission_result(result, text))

    def _display_submission_result(self, result, text_input):
        score = result.get("final_score", 0)
        feedback = result.get("feedback", "No Feedback")
        msg = result.get("msg", "")

        self._show_frame(AppState.RESULT)

        if result["success"]:
            self.result_page.show_success(score, feedback)
            
            if self.active_user:
                self.brain.add_points(self.active_user["nama"], self.active_user["kelas"], score, text_input, result["prediction_level"])
                self.update_leaderboard() 
            
            self._start_auto_reset_timer()
        else:
            self.result_page.show_failure(msg, 
                                          retry_callback=lambda: self._show_frame(AppState.INPUT), 
                                          back_to_home_callback=self.start_reset)

    def _start_auto_reset_timer(self):
        """Starts a timer to automatically reset the app after a successful submission."""
        if self.auto_reset_timer:
            self.after_cancel(self.auto_reset_timer)
        self.auto_reset_timer = self.after(int(AUTO_RESET_AFTER_SUCCESS * 1000), self._reset_app)

    def _cancel_auto_reset_timer(self):
        if self.auto_reset_timer:
            self.after_cancel(self.auto_reset_timer)
            self.auto_reset_timer = None
        
    def _on_closing(self):
        log.info("Application closing. Shutting down services.")
        self.camera_manager.shutdown()
        self._cancel_auto_reset_timer()
        self.destroy()

if __name__ == "__main__":
    ctk.set_appearance_mode("Light")
    ctk.set_default_color_theme("blue")
    
    app = GoodDeedApp()
    app.protocol("WM_DELETE_WINDOW", app._on_closing)
    app.mainloop()