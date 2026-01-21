import customtkinter as ctk
from core.logger import log

class RegisterPage(ctk.CTkFrame):
    def __init__(self, master, submit_callback, cancel_callback, **kwargs):
        super().__init__(master, fg_color="white", corner_radius=15, **kwargs)
        log.info("RegisterPage: Initializing.")

        self.submit_register = submit_callback
        self.cancel_callback = cancel_callback
        
        ctk.CTkLabel(self, text="👋 Halo Teman Baru!", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(40, 10))
        ctk.CTkLabel(self, text="Wajahmu belum terdaftar. Kenalan dulu yuk!", font=ctk.CTkFont(size=14)).pack(pady=5)
        
        self.entry_nama = ctk.CTkEntry(self, placeholder_text="Ketik nama panggilanmu lalu ENTER...", width=300, height=50, font=ctk.CTkFont(size=16))
        self.entry_nama.pack(pady=20)
        
        self.daftar_kelas = ["7-A", "7-B", "7-C", "8-A", "8-B", "8-C", "9-A", "9-B", "9-C"] 
        self.kelas_index = 0
        
        self.lbl_kelas_display = ctk.CTkLabel(self, text=self.daftar_kelas[self.kelas_index], width=300, height=40, font=ctk.CTkFont(size=16), fg_color="#f0f0f0", corner_radius=5)
        self.lbl_kelas_display.pack(pady=10)
        
        self.lbl_submit_hint = ctk.CTkLabel(self, text="Gunakan Panah Atas/Bawah untuk Pilih Kelas", font=ctk.CTkFont(size=12), text_color="gray")
        self.lbl_submit_hint.pack(pady=2)

        self.btn_submit = ctk.CTkButton(self, text="Simpan & Lanjut", command=self.submit_register, width=200, height=40)
        self.btn_submit.pack(pady=20)
        ctk.CTkButton(self, text="Batal", command=self.cancel_callback, fg_color="transparent", text_color="red").pack()

        # Keyboard bindings
        self.bind("<Up>", self.prev_class)
        self.bind("<Down>", self.next_class)

        self.current_state = "ENTRY_NAME"
        self.entry_nama.focus_set()
        log.info("RegisterPage: Initial focus set on name entry in __init__.")

    def handle_enter(self):
        log.info(f"RegisterPage: handle_enter called in state: {self.current_state}")
        if self.current_state == "ENTRY_NAME":
            self.focus_to_kelas()
        elif self.current_state == "SELECT_CLASS":
            self.submit_register()

    def focus_to_kelas(self, event=None):
        log.info("RegisterPage: focus_to_kelas called.")
        nama = self.entry_nama.get()
        if not nama: 
            log.warning("RegisterPage: Name is empty, cannot proceed.")
            return
        
        self.current_state = "SELECT_CLASS"
        log.info("RegisterPage: State changed to SELECT_CLASS.")
        self.entry_nama.configure(state="disabled", fg_color="#e0e0e0")
        self.lbl_kelas_display.configure(text_color="green", font=ctk.CTkFont(size=16, weight="bold"))
        self.lbl_submit_hint.configure(text="[Tekan ENTER untuk KONFIRMASI]", text_color="green")
        self.focus_set() 
        log.info("RegisterPage: Focus set on the frame for class selection.")

    def prev_class(self, event=None):
        if self.current_state == "SELECT_CLASS":
            self.kelas_index = (self.kelas_index - 1) % len(self.daftar_kelas)
            self.update_kelas_display()
            self.focus_set()
            log.info(f"RegisterPage: prev_class. New class: {self.daftar_kelas[self.kelas_index]}")

    def next_class(self, event=None):
        if self.current_state == "SELECT_CLASS":
            self.kelas_index = (self.kelas_index + 1) % len(self.daftar_kelas)
            self.update_kelas_display()
            self.focus_set()
            log.info(f"RegisterPage: next_class. New class: {self.daftar_kelas[self.kelas_index]}")
            
    def update_kelas_display(self):
        pilihan = self.daftar_kelas[self.kelas_index]
        self.lbl_kelas_display.configure(text=pilihan)

    def get_values(self):
        nama = self.entry_nama.get()
        kelas = self.daftar_kelas[self.kelas_index]
        log.info(f"RegisterPage: get_values returning: Name='{nama}', Class='{kelas}'")
        if kelas == "Pilih Kelas":
            kelas = None
        return {"nama": nama, "kelas": kelas}

    def reset(self):
        log.info("RegisterPage: Resetting page state.")
        self.current_state = "ENTRY_NAME"
        self.entry_nama.configure(state="normal", fg_color="white")
        self.entry_nama.delete(0, "end")
        self.kelas_index = 0
        self.update_kelas_display()
        self.lbl_kelas_display.configure(text_color="black", font=ctk.CTkFont(size=16))
        self.lbl_submit_hint.configure(text="Gunakan Panah Atas/Bawah untuk Pilih Kelas", text_color="gray")
        self.entry_nama.focus_set()
        log.info("RegisterPage: Reset complete, focus set on name entry.")

    def set_initial_focus(self):
        log.info("RegisterPage: Setting initial focus with delay.")
        self.after(100, self.entry_nama.focus_set)
        log.info("RegisterPage: after(100, focus_set) called.")
