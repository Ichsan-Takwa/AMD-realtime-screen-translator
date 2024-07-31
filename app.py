import tkinter as tk
from tkinter import ttk
from main_window import MainWindow
from select_window_popup import SelectWindowPopup
from translation_window import TranslationWindow

class WindowManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Window Manager App")
        self.root.geometry("1366x768")
        
        # window style theme
        self.root.option_add("*tearOff", False) # This is always a good idea

        # Make the app responsive
        self.root.columnconfigure(index=0, weight=1)
        self.root.columnconfigure(index=1, weight=1)
        self.root.columnconfigure(index=2, weight=1)
        self.root.rowconfigure(index=0, weight=1)
        self.root.rowconfigure(index=1, weight=1)
        self.root.rowconfigure(index=2, weight=1)

        # # Create a style
        self.style = ttk.Style(self.root)

        # # Import the tcl file
        self.root.tk.call("source", "src/forest-dark.tcl")

        # # Set the theme with the theme_use method
        self.style.theme_use("forest-dark")

        self.main_window = MainWindow(self)
        self.select_window_popup = None
        self.translation_window = None

        self.show_main_menu()

    def show_main_menu(self):
        self.main_window.show()

    def show_select_window_popup(self):
        if not self.select_window_popup:
            self.select_window_popup = SelectWindowPopup(self)
        self.select_window_popup.show()

    def start_translation(self, target_window):
        if not self.translation_window:
            self.translation_window = TranslationWindow(self, target_window)
        self.translation_window.show()

    def stop_translation(self):
        if self.translation_window:
            self.translation_window.hide()
            self.translation_window = None
        self.show_main_menu()

    def clear_frame(self, frame):
        for widget in frame.winfo_children():
            widget.destroy()
