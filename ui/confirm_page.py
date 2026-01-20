import customtkinter as ctk

class ConfirmPage(ctk.CTkFrame):
    def __init__(self, master, yes_callback, no_callback, **kwargs):
        super().__init__(master, fg_color="white", corner_radius=15, **kwargs)

        ctk.CTkLabel(self, text="🤔", font=ctk.CTkFont(size=80)).pack(pady=(50, 10))
        ctk.CTkLabel(self, text="Sebentar, sistem agak ragu...", font=ctk.CTkFont(size=16)).pack(pady=5)
        
        self.lbl_confirm_name = ctk.CTkLabel(self, text="Apakah kamu Budi?", font=ctk.CTkFont(size=24, weight="bold"))
        self.lbl_confirm_name.pack(pady=20)
        
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(pady=20)
        
        ctk.CTkButton(btn_row, text="Bukan, Daftar Baru", command=no_callback, fg_color="red", width=150).pack(side="left", padx=10)
        ctk.CTkButton(btn_row, text="Ya, Itu Aku!", command=yes_callback, fg_color="green", width=150).pack(side="left", padx=10)

    def set_name(self, name):
        self.lbl_confirm_name.configure(text=f"Apakah kamu {name}?")
