import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from PIL import Image, ImageTk
import os
from tqdm import tqdm
import requests
from huggingface_hub import HfApi


class MainWindow:
    def __init__(self, app):
        self.app = app
        self.root = app.root
        self.frame = tk.Frame(self.root)
        self.selected_window_title = tk.StringVar()
        self.translating = False
        self.api = HfApi()
        self.init_ui()

    def init_ui(self):
        self.frame.pack(fill=tk.BOTH, expand=True)
        
        self.bg_image = ImageTk.PhotoImage(Image.open("./src/background.png"))
        self.bg_label = tk.Label(self.frame, image=self.bg_image)
        self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        self.btn_open_window_list = ctk.CTkButton(
            self.frame, 
            command=self.app.show_select_window_popup, 
            fg_color="#247f4c",
            text_color="#DDD", 
            bg_color="#000000",
            image=ctk.CTkImage(light_image=Image.open("./src/translate-icon.png"), dark_image=Image.open("./src/translate-icon.png"), size=(64,64)),
            width=48, 
            height=48, 
            anchor="center",
            compound="top",
            corner_radius=140)
        self.btn_open_window_list.place(relx=0.1, rely=0.7)

        self.selected_window_label = tk.Label(self.frame, textvariable=self.selected_window_title)
        self.selected_window_label.pack(pady=20)

        option_menu_list = ["", "en", "fr", "es", "de", "ru", "sm"]
        self.src_lang_var = tk.StringVar(value="en")
        self.tgt_lang_var = tk.StringVar(value="id")

        self.src_lang_var.trace_add('write', self.check_model_status)
        self.tgt_lang_var.trace_add('write', self.check_model_status)

        self.src_lang_frame = tk.LabelFrame(self.frame, text="From", bg="#000")
        self.src_lang_option = ttk.OptionMenu(self.src_lang_frame, self.src_lang_var, *option_menu_list)
        self.src_lang_option.grid(row=0, column=0, padx=5, pady=10, sticky="nsew")
        self.src_lang_frame.place(relx=0.05, rely=0.4, relwidth=0.2)

        self.dst_lang_frame = tk.LabelFrame(self.frame, text="To", bg="#000")
        self.dst_lang_option = ttk.OptionMenu(self.dst_lang_frame, self.tgt_lang_var, *option_menu_list)
        self.dst_lang_option.grid(row=0, column=0, padx=5, pady=10, sticky="nsew")
        self.dst_lang_frame.place(relx=0.05, rely=0.5, relwidth=0.2)

        self.size_label = tk.Label(self.frame, text="", bg="#000", fg="#DDD")
        self.size_label.place(relx=0.05, rely=0.6, relwidth=0.2)

        self.progress_bar = ttk.Progressbar(self.frame, orient="horizontal", mode="determinate")

        self.check_model_status()

    def show(self):
        self.frame.pack(fill=tk.BOTH, expand=True)

    def hide(self):
        self.frame.pack_forget()

    def check_model_status(self, *args):
        src_lang = self.src_lang_var.get()
        tgt_lang = self.tgt_lang_var.get()
        
        if src_lang and tgt_lang:
            model_name = f'Helsinki-NLP/opus-mt-{src_lang}-{tgt_lang}'
            model_dir = os.path.join(os.path.expanduser('~'), '.cache', 'huggingface', 'hub', 'models--' + model_name.replace('/', '--'))
            if os.path.exists(model_dir):
                self.api.model_info(model_name)
                self.update_button_status(model_downloaded=True)
            else:
                files = self.api.list_repo_files(model_name)
                
                self.size_label.config(text=f"Model size between 300MB-1GB")
                self.update_button_status(model_downloaded=False)

    def update_button_status(self, model_downloaded):
        if model_downloaded:
            self.btn_open_window_list.configure(text="Start Translate", command=self.app.show_select_window_popup)
            self.size_label.config(text="")
        else:
            self.btn_open_window_list.configure(text="Download Model", command=self.download_model)

    def download_model(self):
        src_lang = self.src_lang_var.get()
        tgt_lang = self.tgt_lang_var.get()
        model_name = f'Helsinki-NLP/opus-mt-{src_lang}-{tgt_lang}'
        self.progress_bar.place(relx=0.05, rely=0.65, relwidth=0.2)
        self.progress_bar.start()

        def download():
            model_path = f"models/{model_name}"
            if not os.path.exists(model_path):
                os.makedirs(model_path)
            files = self.api.list_repo_files(model_name)
            total_size = sum(file.size for file in files if hasattr(file, 'size'))
            for file in tqdm(files, desc="Downloading model", unit="file"):
                file_url = file.rfilename
                file_path = os.path.join(model_path, file_url)
                response = requests.get(f"https://huggingface.co/{model_name}/resolve/main/{file_url}", stream=True)
                with open(file_path, "wb") as f:
                    for data in tqdm(response.iter_content(1024), total=total_size // 1024, unit="KB", desc=file_url):
                        f.write(data)
                        self.progress_bar["value"] += (len(data) / total_size) * 100
                self.progress_bar.stop()
                self.progress_bar.place_forget()