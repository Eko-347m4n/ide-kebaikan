import customtkinter as ctk

class RegisterPage(ctk.CTkFrame):
    def __init__(self, master, submit_callback, cancel_callback, **kwargs):
        super().__init__(master, fg_color="white", corner_radius=15, **kwargs)

        ctk.CTkLabel(self, text="👋 Halo Teman Baru!", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(40, 10))
        ctk.CTkLabel(self, text="Wajahmu belum terdaftar. Kenalan dulu yuk!", font=ctk.CTkFont(size=14)).pack(pady=5)
        
        self.entry_nama = ctk.CTkEntry(self, placeholder_text="Nama Panggilanmu?", width=300, height=40)
        self.entry_nama.pack(pady=10)
        
        # TODO: This class list could be loaded from a config file or passed during initialization
        self.daftar_kelas = ["7-A"] 
        self.entry_kelas = ctk.CTkOptionMenu(self, values=self.daftar_kelas, width=300, height=40)
        self.entry_kelas.pack(pady=10)
        self.entry_kelas.set("Pilih Kelas") 
        
        ctk.CTkButton(self, text="Simpan & Lanjut", command=submit_callback, width=200, height=40).pack(pady=20)
        ctk.CTkButton(self, text="Batal", command=cancel_callback, fg_color="transparent", text_color="red").pack()

    def get_values(self):
        """Returns the current values from the entry fields."""
        nama = self.entry_nama.get()
        kelas = self.entry_kelas.get()
        if kelas == "Pilih Kelas":
            kelas = None
        return {"nama": nama, "kelas": kelas}

    def reset(self):
        """Resets the entry fields to their default state."""
        self.entry_nama.delete(0, "end")
        self.entry_kelas.set("Pilih Kelas")
