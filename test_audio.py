import pygame
import os
import time

try:
    pygame.init()
    pygame.mixer.init()
    
    bgm_path = "assets/sounds/bgm_fixed.mp3"
    print(f"Testing audio file: {bgm_path}")
    
    if not os.path.exists(bgm_path):
        print("Error: File not found!")
        exit(1)
        
    pygame.mixer.music.load(bgm_path)
    pygame.mixer.music.set_volume(1.0)
    pygame.mixer.music.play()
    
    print("Playing music... (Press Ctrl+C to stop)")
    while pygame.mixer.music.get_busy():
        time.sleep(1)
        
except Exception as e:
    print(f"Error: {e}")
