import customtkinter as ctk
import random
from core.constants import (
    COLOR_CONF_BG, COLOR_SUCCESS_BORDER, RESULT_TITLE,
    RESULT_SUCCESS_ICON_HIGH, RESULT_SUCCESS_ICON_LOW,
    COLOR_SCORE, COLOR_FAILURE_BORDER, RESULT_FAILURE_ICON
)

class ResultPage(ctk.CTkFrame):
    def __init__(self, master, reset_callback, **kwargs):
        super().__init__(master, fg_color=COLOR_CONF_BG, corner_radius=15, **kwargs)
        
        # Store callbacks
        self._reset_callback = reset_callback
        self._retry_callback = None # Will be set during show_failure

        self.result_card = ctk.CTkFrame(self, fg_color="white", corner_radius=20, 
                                        border_width=2, border_color=COLOR_SUCCESS_BORDER)
        self.result_card.place(relx=0.5, rely=0.5, anchor="center", relwidth=1, relheight=1)
        
        self.lbl_result_title = ctk.CTkLabel(self.result_card, text=RESULT_TITLE, 
                                             font=ctk.CTkFont(size=14, weight="bold"), text_color="gray")
        self.lbl_result_title.pack(pady=(30, 10))
        
        self.lbl_icon = ctk.CTkLabel(self.result_card, text=RESULT_SUCCESS_ICON_HIGH, font=ctk.CTkFont(size=80))
        self.lbl_icon.pack(pady=5)
        
        self.lbl_score = ctk.CTkLabel(self.result_card, text="100", 
                                      font=ctk.CTkFont(size=70, weight="bold"), text_color=COLOR_SCORE) 
        self.lbl_score.pack(pady=5)
        
        self.lbl_feedback = ctk.CTkLabel(self.result_card, text="Feedback...", 
                                         font=ctk.CTkFont(size=18), wraplength=400)
        self.lbl_feedback.pack(pady=20)
        
        # Button Container for failure state
        self.button_frame = ctk.CTkFrame(self.result_card, fg_color="transparent")
        self.button_frame.pack(side="bottom", pady=10)
        
        # Primary action button (Selesai for success, Perbaiki for failure)
        self.btn_primary_action = ctk.CTkButton(self.button_frame, text="Selesai", command=self._reset_callback, width=150, height=40, corner_radius=20)
        self.btn_primary_action.pack(side="left", padx=2)

        # Secondary action button (Back to Home for failure)
        self.btn_secondary_action = ctk.CTkButton(self.button_frame, text="Kembali ke Utama", command=self._reset_callback, width=150, height=40, corner_radius=20, fg_color="gray", hover_color="darkgray")
        self.btn_secondary_action.pack_forget()

    def show_success(self, score, feedback):
        self.result_card.lift()
        self.result_card.configure(border_color=COLOR_SUCCESS_BORDER)
        self.lbl_icon.configure(text=RESULT_SUCCESS_ICON_HIGH if score >= 80 else RESULT_SUCCESS_ICON_LOW)
        self.lbl_score.configure(text_color=COLOR_SCORE)
        self.lbl_feedback.configure(text=feedback, text_color="black")
        
        self.animate_score_pop(target_score=score, current_size=10)
        
        self.btn_primary_action.configure(text="Selesai (Reset)", fg_color="blue", hover_color="darkblue", command=self._reset_callback)
        self.btn_secondary_action.pack_forget() # Ensure secondary button is hidden

    def show_failure(self, msg, retry_callback, back_to_home_callback):
        self._retry_callback = retry_callback # Store this for the "Perbaiki" button
        self._reset_callback = back_to_home_callback # Store this for the "Kembali ke Utama" button

        self.result_card.lift()
        self.result_card.configure(border_color=COLOR_FAILURE_BORDER)
        self.lbl_icon.configure(text=RESULT_FAILURE_ICON)
        self.lbl_score.configure(text="0", text_color="red")
        self.lbl_feedback.configure(text=f"{msg}\n\nWah aku masih belum menangkap maksudmu nih tolong jelasin dong idemu lebih jelas lagi!", text_color="red")
        
        self.btn_primary_action.configure(text="Perbaiki Kata-kata ✏️", fg_color="green", hover_color="darkgreen", command=self._retry_callback)
        
        self.btn_secondary_action.configure(text="Kembali ke Utama", command=self._reset_callback)
        self.btn_secondary_action.pack(side="right", padx=2) # Show the secondary button

    def animate_score_pop(self, target_score, current_size):
        if current_size >= 70: 
            self.lbl_score.configure(text=f"{target_score}") 
            return
        
        temp_score = random.randint(0, 100) if current_size < 60 else target_score
        self.lbl_score.configure(font=ctk.CTkFont(size=current_size, weight="bold"), text=f"{temp_score}")
        
        self.after(20, lambda: self.animate_score_pop(target_score, current_size + 5))