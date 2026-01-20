import customtkinter as ctk

class LoadingPage(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="white", corner_radius=15, **kwargs)
        
        self.lbl_loading = ctk.CTkLabel(self, text="Sedang menghubungi markas...", font=ctk.CTkFont(size=20))
        self.lbl_loading.pack(expand=True)

    def set_text(self, text):
        self.lbl_loading.configure(text=text)
