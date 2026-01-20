import customtkinter as ctk

class InputPage(ctk.CTkFrame):
    def __init__(self, master, submit_callback, cancel_callback, **kwargs):
        super().__init__(master, fg_color="white", corner_radius=15, **kwargs)

        self.lbl_welcome = ctk.CTkLabel(self, text="Hai, Budi!", font=ctk.CTkFont(size=24, weight="bold"))
        self.lbl_welcome.pack(pady=(40, 10))
        
        ctk.CTkLabel(self, text="Ide kebaikan apa yang ingin kamu bagikan?", font=ctk.CTkFont(size=16)).pack(pady=10)
        
        self.txt_ide = ctk.CTkTextbox(self, width=400, height=150, font=ctk.CTkFont(size=14))
        self.txt_ide.pack(pady=10)
        
        ctk.CTkButton(self, text="Kirim Kebaikan 🚀", command=submit_callback, width=200, height=50, fg_color="green").pack(pady=20)
        
        self.btn_cancel_input = ctk.CTkButton(self, text="Batal / Kembali", command=cancel_callback, fg_color="transparent", text_color="red", hover_color="#ffebee")
        self.btn_cancel_input.pack(pady=5)

    def set_welcome_message(self, name):
        """Sets the welcome message with the user's name."""
        self.lbl_welcome.configure(text=f"Hai, {name}!")

    def get_idea_text(self):
        """Returns the text from the textbox."""
        return self.txt_ide.get("1.0", "end-1c")

    def reset(self):
        """Clears the textbox and sets focus."""
        self.txt_ide.delete("1.0", "end")
    
    def focus_textbox(self):
        self.txt_ide.focus_set()

