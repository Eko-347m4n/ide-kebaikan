import customtkinter as ctk
from core.constants import CAM_CLICK_TO_START, CAM_INFO_SLEEP

class CameraPage(ctk.CTkFrame):
    def __init__(self, master, wake_up_callback, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        
        self.cam_container = ctk.CTkFrame(self, corner_radius=15, fg_color="white")
        self.cam_container.pack(fill="both", expand=True)
        
        self.cam_label = ctk.CTkLabel(self.cam_container, 
                                      text=CAM_CLICK_TO_START,
                                      font=ctk.CTkFont(size=20, weight="bold"), text_color="gray")
        self.cam_label.pack(fill="both", expand=True, padx=0, pady=0)        
        self.cam_label.bind('<Button-1>', wake_up_callback)
        
        self.info_label = ctk.CTkLabel(self, text=CAM_INFO_SLEEP, font=ctk.CTkFont(size=20, weight="bold"), text_color="gray")
        self.info_label.pack(pady=15)

    def set_info_text(self, text, color="gray"):
        self.info_label.configure(text=text, text_color=color)

    def set_cam_image(self, image):
        self.cam_label.configure(image=image)
        self.cam_label.image = image
    
    def clear_cam_image(self):
        self.cam_label.configure(image=None)
        self.cam_label.image = None

    def set_cam_text(self, text, color="gray"):
        self.cam_label.configure(text=text, text_color=color)
