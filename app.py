import customtkinter as ctk
from PIL import Image, ImageTk
import cv2
import threading
import time

from core.brain import BrainLogic
from core.vision import VisionSystem

ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")

class KebaikanApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- SETUP WINDOW ---
        self.title("AI Kebaikan - Smart Kindness Detector")
        self.geometry("1100x700")
        
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- SYSTEM ---
        self.brain = BrainLogic()
        self.vision = VisionSystem()
        
        users = self.brain.get_all_users()
        self.vision.load_memory(users)

        # STATE
        self.current_state = "STANDBY" 
        self.active_user = None         
        self.pending_encoding = None    

        # UI
        self.setup_sidebar()
        self.setup_main_area()

        # CAMERA
        self.cap = cv2.VideoCapture(0)
        self.update_camera() 

    def setup_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(4, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar, text="🤖 AI KEBAIKAN", font=ctk.CTkFont(size=24, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(30, 10))

        self.status_label = ctk.CTkLabel(self.sidebar, text="System: ONLINE ✅", text_color="green", font=ctk.CTkFont(weight="bold"))
        self.status_label.grid(row=1, column=0, padx=20, pady=0)

        ctk.CTkLabel(self.sidebar, text="_________________________").grid(row=2, column=0, pady=10)

        self.lb_title = ctk.CTkLabel(self.sidebar, text="🏆 Top Siswa", font=ctk.CTkFont(size=18, weight="bold"))
        self.lb_title.grid(row=3, column=0, padx=20, pady=(10, 10))

        self.lb_frame = ctk.CTkScrollableFrame(self.sidebar, label_text="Minggu Ini", fg_color="white")
        self.lb_frame.grid(row=4, column=0, padx=20, pady=10, sticky="nsew")
        self.refresh_leaderboard() 

        self.btn_reset = ctk.CTkButton(self.sidebar, text="Reset System", command=self.reset_system, fg_color="transparent", border_width=1, text_color=("gray10", "gray90"))
        self.btn_reset.grid(row=5, column=0, padx=20, pady=20)

    def refresh_leaderboard(self):
        for widget in self.lb_frame.winfo_children():
            widget.destroy()
            
        data = self.brain.get_leaderboard(10)
        if not data:
            ctk.CTkLabel(self.lb_frame, text="Belum ada data.").pack()
            return
            
        for idx, (nama, kelas, poin) in enumerate(data):
            row = ctk.CTkFrame(self.lb_frame, fg_color="transparent")
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=f"{idx+1}. {nama} ({kelas})", anchor="w").pack(side="left", padx=5)
            ctk.CTkLabel(row, text=f"{poin} Pts", font=ctk.CTkFont(weight="bold")).pack(side="right", padx=5)

    def setup_main_area(self):
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        
        # --- HALAMAN 1: KAMERA ---
        self.page_camera = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.cam_container = ctk.CTkFrame(self.page_camera, corner_radius=15, fg_color="white")
        self.cam_container.pack(fill="both", expand=True)
        self.cam_label = ctk.CTkLabel(self.cam_container, text="")
        self.cam_label.pack(fill="both", expand=True, padx=10, pady=10)
        self.info_label = ctk.CTkLabel(self.page_camera, text="Senyum untuk Login 😊", font=ctk.CTkFont(size=20, weight="bold"), text_color="blue")
        self.info_label.pack(pady=15)

        # --- HALAMAN 2: REGISTER ---
        self.page_register = ctk.CTkFrame(self.main_frame, fg_color="white", corner_radius=15)
        ctk.CTkLabel(self.page_register, text="👋 Halo Teman Baru!", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(40, 10))
        ctk.CTkLabel(self.page_register, text="Wajahmu belum terdaftar. Kenalan dulu yuk!", font=ctk.CTkFont(size=14)).pack(pady=5)
        self.entry_nama = ctk.CTkEntry(self.page_register, placeholder_text="Nama Lengkap", width=300, height=40)
        self.entry_nama.pack(pady=10)
        self.daftar_kelas = ["10-A", "10-B", "11-A", "11-B", "12-A", "12-B", "Guru/Staff"]
        self.entry_kelas = ctk.CTkOptionMenu(self.page_register, values=self.daftar_kelas, width=300, height=40)
        self.entry_kelas.pack(pady=10)
        self.entry_kelas.set("Pilih Kelas") 
        ctk.CTkButton(self.page_register, text="Simpan & Lanjut", command=self.submit_register, width=200, height=40).pack(pady=20)
        ctk.CTkButton(self.page_register, text="Batal", command=self.reset_system, fg_color="transparent", text_color="red").pack()

        # --- HALAMAN 3: INPUT ---
        self.page_input = ctk.CTkFrame(self.main_frame, fg_color="white", corner_radius=15)
        self.lbl_welcome = ctk.CTkLabel(self.page_input, text="Hai, Budi!", font=ctk.CTkFont(size=24, weight="bold"))
        self.lbl_welcome.pack(pady=(40, 10))
        ctk.CTkLabel(self.page_input, text="Kebaikan apa yang kamu lakukan hari ini?", font=ctk.CTkFont(size=16)).pack(pady=10)
        self.txt_ide = ctk.CTkTextbox(self.page_input, width=400, height=150, font=ctk.CTkFont(size=14))
        self.txt_ide.pack(pady=10)
        ctk.CTkButton(self.page_input, text="Kirim Kebaikan 🚀", command=self.submit_kebaikan, width=200, height=50, fg_color="green").pack(pady=20)
        
        # --- HALAMAN 4: RESULT ---
        self.page_result = ctk.CTkFrame(self.main_frame, fg_color="white", corner_radius=15)
        self.lbl_score = ctk.CTkLabel(self.page_result, text="100", font=ctk.CTkFont(size=60, weight="bold"), text_color="orange")
        self.lbl_score.pack(pady=(50, 10))
        self.lbl_feedback = ctk.CTkLabel(self.page_result, text="Feedback AI...", font=ctk.CTkFont(size=18), wraplength=500)
        self.lbl_feedback.pack(pady=20)
        
        # [FIX UI] Tombol ini nanti teks dan fungsinya berubah dinamis (Selesai / Coba Lagi)
        self.btn_result_action = ctk.CTkButton(self.page_result, text="Selesai", command=self.reset_system, width=200)
        self.btn_result_action.pack(pady=30)

        self.show_frame("CAMERA")

    def show_frame(self, name):
        self.page_camera.pack_forget()
        self.page_register.pack_forget()
        self.page_input.pack_forget()
        self.page_result.pack_forget()

        if name == "CAMERA":
            self.page_camera.pack(fill="both", expand=True)
            self.current_state = "STANDBY"
        elif name == "REGISTER":
            self.page_register.pack(fill="both", expand=True, padx=50, pady=50)
            self.current_state = "REGISTER"
        elif name == "INPUT":
            self.page_input.pack(fill="both", expand=True, padx=50, pady=50)
            self.current_state = "INPUT"
            self.txt_ide.delete("1.0", "end")
            self.txt_ide.focus_set()
        elif name == "RESULT":
            self.page_result.pack(fill="both", expand=True, padx=50, pady=50)
            self.current_state = "RESULT"

    def update_camera(self):
        if self.current_state == "STANDBY":
            ret, frame = self.cap.read()
            if ret:
                frame = cv2.flip(frame, 1)
                data = self.vision.process_frame(frame)
                
                if data["face_detected"] and data["location"]:
                    top, right, bottom, left = data["location"]
                    zone = data["zone"]
                    
                    color = (0, 0, 255) 
                    if zone == "GREEN": color = (0, 255, 0)
                    elif zone == "YELLOW": color = (0, 255, 255)
                    
                    cv2.rectangle(frame, (left, top), (right, bottom), color, 3)

                    if data["is_smiling"]:
                        self.handle_login_trigger(data)

                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame_rgb)
                img_tk = ctk.CTkImage(light_image=img, dark_image=img, size=(640, 480))
                self.cam_label.configure(image=img_tk)
                self.cam_label.image = img_tk 

        self.after(10, self.update_camera)

    def handle_login_trigger(self, data):
        zone = data["zone"]
        
        if zone == "RED":
            # Wajah Asing -> Masuk Pendaftaran
            self.pending_encoding = data["encoding"] 
            self.show_frame("REGISTER")
        else:
            # Wajah Dikenal -> Masuk Input
            user = data["user_data"]
            self.active_user = user
            self.lbl_welcome.configure(text=f"Hai, {user['nama']}!")
            self.show_frame("INPUT")

    def submit_register(self):
        nama = self.entry_nama.get()
        kelas = self.entry_kelas.get()
        if not nama or kelas == "Pilih Kelas": return 
            
        if self.pending_encoding is not None:
            success, msg = self.brain.register_user(nama, kelas, self.pending_encoding)
            if success:
                users = self.brain.get_all_users()
                self.vision.load_memory(users)
                self.active_user = {"nama": nama, "kelas": kelas}
                self.lbl_welcome.configure(text=f"Hai, {nama}!")
                self.show_frame("INPUT")
            else:
                print(f"Error Register: {msg}")

    def submit_kebaikan(self):
        text = self.txt_ide.get("1.0", "end-1c")
        if len(text) < 5: return 
        
        result = self.brain.predict_and_score(text)
        
        score = result.get("final_score", 0)
        feedback = result.get("feedback", "No Feedback")
        msg = result.get("msg", "")

        if result["success"]:
            # SUKSES
            self.lbl_score.configure(text=f"{score}", text_color="orange")
            self.lbl_feedback.configure(text=feedback, text_color="black")
            
            if self.active_user:
                self.brain.add_points(self.active_user["nama"], self.active_user["kelas"], score, text, result["prediction_level"])
                self.refresh_leaderboard() 
            
            # Tombol "Selesai" -> Reset ke awal
            self.btn_result_action.configure(text="Selesai (Reset)", fg_color="blue", command=self.reset_system)
            self.show_frame("RESULT")
            
        else:
            # GAGAL (JUNK / PENOLAKAN)
            self.lbl_score.configure(text="0", text_color="red")
            
            # Tampilkan pesan error (msg) di label feedback
            self.lbl_feedback.configure(text=f"⚠️ {msg}\n\nSilakan perbaiki kalimatmu ya.", text_color="red")
            
            # [FIX UX] Tombol "Perbaiki" -> Balik ke halaman Input
            self.btn_result_action.configure(text="Perbaiki Kata-kata", fg_color="green", command=lambda: self.show_frame("INPUT"))
            self.show_frame("RESULT")

    def reset_system(self):
        self.entry_nama.delete(0, "end")
        self.entry_kelas.set("Pilih Kelas")
        self.txt_ide.delete("1.0", "end")
        self.active_user = None
        self.pending_encoding = None
        self.show_frame("CAMERA")

    def on_closing(self):
        self.cap.release()
        self.destroy()

if __name__ == "__main__":
    app = KebaikanApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()