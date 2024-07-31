import tkinter as tk
import threading
import pyautogui
import pygetwindow as gw
from PIL import ImageTk, Image
from process_image import Tesserract, OEM_OPTION, PSM_OPTION, overlay_translated_text
import time

class TranslationWindow:
    def __init__(self, app, target_window):
        self.app = app
        self.window = target_window
        self.root = app.root
        
        self.translating = False
        self.init_ui(self.window)

    def init_ui(self, target_window):
        self.translation_window = tk.Toplevel(self.root)
        selected_title = target_window.title
        if len(selected_title) > 20:
            self.translation_window.title(f"Translating {selected_title[:20]}...")
        self.translation_window.title(f"Translating {selected_title}")


        self.translation_window.protocol("WM_DELETE_WINDOW", self.stop_translation)
        
        print(selected_title)
        self.selected_window = gw.getWindowsWithTitle(selected_title)[0]
        # Move the selected window to the left
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        gap = 10  # Gap between the windows
        self.selected_window.moveTo(0, 0)
        self.selected_window.resizeTo(screen_width // 2 - gap, screen_height)
        
        # Move this app window to the right
        self.translation_window.geometry(f"{screen_width // 2 - gap}x{screen_height}+{screen_width // 2 + gap}+0")
  
        # self.exit_button.pack(side=tk.BOTTOM, fill=tk.X)
        self.screenshot_frame = tk.Frame(self.translation_window)
        self.screenshot_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.screenshot_label = tk.Label(self.screenshot_frame)
        self.screenshot_label.pack(fill=tk.BOTH, expand=True)
        
        self.start_translation(target_window)

    def show(self):
        self.frame.pack(fill=tk.BOTH, expand=True)
        self.start_translation()

    def start_translation(self, target_window):
        ocr = Tesserract(OEM_OPTION.oem_3, PSM_OPTION.psm_3)
        self.screenshot_thread = threading.Thread(target=self.update_screenshot, args=(ocr, self.window, ))
        self.screenshot_thread.start()
        self.root.protocol("WM_DELETE_WINDOW", lambda : self.screenshot_thread.join())
        
    def update_screenshot(self, ocr, selected_window):
        while True:
            # try:
                time.sleep(0.1)
                screenshot = pyautogui.screenshot(region=selected_window.box)
                image = overlay_translated_text(screenshot, ocr)
                image = Image.fromarray(image)
                screenshot = ImageTk.PhotoImage(image)
                
                self.screenshot_label.config(image=screenshot)
                self.screenshot_label.image = screenshot
                time.sleep(0.4)
                print("thread is running")
            # except e:
            #     print("thread stopped")
    
    def stop_translation(self):
        self.translating = False
        self.selected_window_title.set("")
        self.root.deiconify()
        self.translation_window.destroy()
        self.app.main_window.show()


    def translate_loop(self):
        while self.translating:
            screenshot = pyautogui.screenshot(region=(self.window.left, self.window.top, self.window.width, self.window.height))
            translated_text = self.process_image(screenshot)
            overlay_translated_text(screenshot, translated_text, self.window)
            time.sleep(2)

    def process_image(self, image):
        tess = Tesserract()
        text = tess.image_to_text(image, oem=OEM_OPTION, psm=PSM_OPTION)
        translated_text = self.translate_text(text)
        return translated_text

    def translate_text(self, text):
        src_lang = self.app.main_window.src_lang_var.get()
        tgt_lang = self.app.main
