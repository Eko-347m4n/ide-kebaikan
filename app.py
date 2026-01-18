import customtkinter as ctk
from PIL import Image, ImageTk
import cv2
import threading
import time
import random

from core.brain import BrainLogic
from core.vision import VisionSystem

ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")

class ConfettiParticle:
    def __init__(self, canvas, width, height):
        self.canvas = canvas
        self.x = random.randint(0, width)
        self.y = random.randint(-height, 0) 
        self.speed = random.randint(2, 7)
        self.color = random.choice(["red", "green", "blue", "yellow", "orange", "purple", "cyan"])
        self.size = random.randint(5, 10)
        self.id = canvas.create_oval(self.x, self.y, self.x+self.size, self.y+self.size, fill=self.color, outline="")

    def move(self):
        self.y += self.speed
        self.x += random.randint(-1, 1) 
        self.canvas.move(self.id, 0, self.speed)

class ConfettiManager:
    def __init__(self, master_frame):
        self.canvas = ctk.CTkCanvas(master_frame, width=800, height=600, highlightthickness=0, bg="#F0F0F0")
        self.particles = []
        self.is_active = False

    def start(self):
        self.canvas.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.particles = [ConfettiParticle(self.canvas, 1000, 600) for _ in range(50)] # 50 partikel
        self.is_active = True
        self.animate()

    def animate(self):
        if not self.is_active: return
        for p in self.particles:
            p.move()
            if p.y > 700:
                p.y = random.randint(-100, 0)
                self.canvas.move(p.id, 0, -700 - random.randint(0, 100))
        
        self.canvas.after(20, self.animate)

    def stop(self):
        self.is_active = False
        self.canvas.place_forget() 
        for p in self.particles:
            self.canvas.delete(p.id)
        self.particles = []

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
        self.smile_start_time = None
        self.active_user = None         
        self.pending_encoding = None
        self.auto_close_timer = None    

        # UI
        self.setup_sidebar()
        self.setup_main_area()
        self.confetti = ConfettiManager(self.page_result)

        # CAMERA
        self.cap = cv2.VideoCapture(0)
        self.update_camera() 

    def setup_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(4, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar, text="✨ BERBURU IDE KEBAIKAN ✨", font=ctk.CTkFont(size=24, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(30, 10))

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
        self.entry_nama = ctk.CTkEntry(self.page_register, placeholder_text="Nama Panggilanmu?", width=300, height=40)
        self.entry_nama.pack(pady=10)
        self.daftar_kelas = ["7-A"]
        self.entry_kelas = ctk.CTkOptionMenu(self.page_register, values=self.daftar_kelas, width=300, height=40)
        self.entry_kelas.pack(pady=10)
        self.entry_kelas.set("Pilih Kelas") 
        ctk.CTkButton(self.page_register, text="Simpan & Lanjut", command=self.submit_register, width=200, height=40).pack(pady=20)
        ctk.CTkButton(self.page_register, text="Batal", command=self.reset_system, fg_color="transparent", text_color="red").pack()

        # --- HALAMAN 3: INPUT ---
        self.page_input = ctk.CTkFrame(self.main_frame, fg_color="white", corner_radius=15)
        self.lbl_welcome = ctk.CTkLabel(self.page_input, text="Hai, Budi!", font=ctk.CTkFont(size=24, weight="bold"))
        self.lbl_welcome.pack(pady=(40, 10))
        ctk.CTkLabel(self.page_input, text="Ide kebaikan apa yang ingin kamu bagikan?", font=ctk.CTkFont(size=16)).pack(pady=10)
        self.txt_ide = ctk.CTkTextbox(self.page_input, width=400, height=150, font=ctk.CTkFont(size=14))
        self.txt_ide.pack(pady=10)
        ctk.CTkButton(self.page_input, text="Kirim Kebaikan 🚀", command=self.submit_kebaikan, width=200, height=50, fg_color="green").pack(pady=20)
        
        self.page_loading = ctk.CTkFrame(self.main_frame, fg_color="white", corner_radius=15)
        self.lbl_loading = ctk.CTkLabel(self.page_loading, text="Sedang menghubungi markas...", font=ctk.CTkFont(size=20))
        self.lbl_loading.pack(expand=True)

        # --- HALAMAN 4: RESULT ---
        self.page_result = ctk.CTkFrame(self.main_frame, fg_color="#F0F0F0", corner_radius=15)
        self.result_card = ctk.CTkFrame(self.page_result, fg_color="white", corner_radius=20, 
                                        border_width=2, border_color="#FFD700")
        self.result_card.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.6, relheight=0.7)

        # Isi Kartu
        self.lbl_result_title = ctk.CTkLabel(self.result_card, text="✨ HASIL ANALISIS ✨", 
                                             font=ctk.CTkFont(size=14, weight="bold"), text_color="gray")
        self.lbl_result_title.pack(pady=(30, 10))

        # Ikon Emoji Besar (Gimmick)
        self.lbl_icon = ctk.CTkLabel(self.result_card, text="🏆", font=ctk.CTkFont(size=80))
        self.lbl_icon.pack(pady=5)

        # Skor dengan Font Raksasa
        self.lbl_score = ctk.CTkLabel(self.result_card, text="100", 
                                      font=ctk.CTkFont(size=70, weight="bold"), text_color="#FFA500") # Warna Oranye
        self.lbl_score.pack(pady=5)
        
        # Feedback
        self.lbl_feedback = ctk.CTkLabel(self.result_card, text="Feedback...", 
                                         font=ctk.CTkFont(size=18), wraplength=400)
        self.lbl_feedback.pack(pady=20)
        
        # Tombol Action
        self.btn_result_action = ctk.CTkButton(self.result_card, text="Selesai", 
                                               command=self.reset_system, width=200, height=40, corner_radius=20)
        self.btn_result_action.pack(side="bottom", pady=30)
        
        self.show_frame("CAMERA")

    def show_frame(self, name):
        self.page_camera.pack_forget()
        self.page_register.pack_forget()
        self.page_input.pack_forget()
        self.page_loading.pack_forget()
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
        elif name == "LOADING":
            self.page_loading.pack(fill="both", expand=True, padx=50, pady=50)
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
                        if self.smile_start_time is None:
                            self.smile_start_time = time.time() 
                        
                        elapsed = time.time() - self.smile_start_time
                        progress = min(elapsed / 3.0, 1.0)

                        bar_w = 200
                        bx, by = left + (right-left)//2 - bar_w//2, top - 30
                        cv2.rectangle(frame, (bx, by), (bx + bar_w, by + 10), (200, 200, 200), -1)
                        
                        # Bar Hijau (Isi sesuai progress)
                        fill_w = int(bar_w * progress)
                        cv2.rectangle(frame, (bx, by), (bx + fill_w, by + 10), (0, 255, 0), -1)
                        
                        cv2.putText(frame, "TETAP TERSENYUM...", (bx, by-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

                        if elapsed >= 3.0:
                            self.smile_start_time = None 
                            self.handle_login_trigger(data) 
                    
                    else:
                        self.smile_start_time = None

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

        self.show_frame("LOADING")
        self.after(100, lambda: self._process_ai_delayed(text))

    def _process_ai_delayed(self, text):
        result = self.brain.predict_and_score(text)

        self.lbl_loading.configure(text="Menganalisis kadar kebaikanmu nih 🧐")
        self.after(1000, lambda: self.lbl_loading.configure(text="Menghitung poin..."))
        self.after(2000, lambda:self._show_final_result(result, text))

    def _show_final_result(self, result, text_input):
        score = result.get("final_score", 0)
        feedback = result.get("feedback", "No Feedback")
        msg = result.get("msg", "")

        self.show_frame("RESULT")

        if result["success"]:
            self.start_confetti()
        self.result_card.lift()

        if result["success"]:
            self.result_card.configure(border_color="#FFD700") # Emas
            self.lbl_icon.configure(text="🏆" if score >= 80 else "⭐") # Ikon beda sesuai skor
            self.lbl_score.configure(text_color="#FFA500") # Oranye
            self.lbl_feedback.configure(text=feedback, text_color="black")         
            self.animate_score_pop(target_score=score, current_size=10)
            
            if self.active_user:
                self.brain.add_points(self.active_user["nama"], self.active_user["kelas"], score, text_input, result["prediction_level"])
                self.refresh_leaderboard() 
            
            self.btn_result_action.configure(text="Selesai (Reset)", fg_color="blue", hover_color="darkblue", command=self.reset_system)
            self.start_auto_close_timer()
            
        else:
            self.stop_confetti() 
            self.result_card.configure(border_color="red") 
            self.lbl_icon.configure(text="🚫")
            self.lbl_score.configure(text="0", text_color="red")
            self.lbl_feedback.configure(text=f"{msg}\n\nYuk perbaiki kalimatmu!", text_color="red")            
            self.btn_result_action.configure(text="Perbaiki Kata-kata ✏️", fg_color="green", hover_color="darkgreen", command=lambda: self.show_frame("INPUT"))

    def animate_score_pop(self, target_score, current_size):
        if current_size >= 70: 
            self.lbl_score.configure(text=f"{target_score}") # Pastikan angka final benar
            return
        
        temp_score = random.randint(0, 100) if current_size < 60 else target_score
        self.lbl_score.configure(font=ctk.CTkFont(size=current_size, weight="bold"), text=f"{temp_score}")
        
        # Loop lagi dengan ukuran lebih besar
        self.after(20, lambda: self.animate_score_pop(target_score, current_size + 5))
    
    def start_auto_close_timer(self):
        # Batalkan timer lama kalau ada
        if self.auto_close_timer:
            self.after_cancel(self.auto_close_timer)
        
        # Set timer baru 7 detik -> Panggil reset_system
        self.auto_close_timer = self.after(7000, self.reset_system)

    def cancel_auto_close(self):
        # Dipanggil kalau user klik tombol "Selesai" manual
        if self.auto_close_timer:
            self.after_cancel(self.auto_close_timer)
            self.auto_close_timer = None
        
    def reset_system(self):
        self.cancel_auto_close()
        self.stop_confetti()
        self.entry_nama.delete(0, "end")
        self.entry_kelas.set("Pilih Kelas")
        self.txt_ide.delete("1.0", "end")
        self.active_user = None
        self.pending_encoding = None
        self.show_frame("CAMERA")

    def on_closing(self):
        self.cap.release()
        self.destroy()
    
    def start_confetti(self):
        self.confetti.start()

    def stop_confetti(self):
        self.confetti.stop()

if __name__ == "__main__":
    app = KebaikanApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()