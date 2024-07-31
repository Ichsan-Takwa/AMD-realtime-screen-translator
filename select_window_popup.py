import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import pygetwindow as gw
import win32gui
import win32ui
import win32con

class SelectWindowPopup:
    def __init__(self, app):
        self.app = app
        self.root = app.root
        self.popup = None
        self.preview_images = []

    def show(self):
        self.popup = tk.Toplevel(self.root)
        self.popup.title("Select a Window")
        self.popup.geometry("1068x600")
        self.popup.resizable(False, False)
        self.popup.transient(self.root)
        self.popup.grab_set()

        canvas = tk.Canvas(self.popup)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(self.popup, orient=tk.VERTICAL, command=canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))

        window_list_frame = tk.Frame(canvas)
        canvas.create_window((0, 0), window=window_list_frame, anchor='nw')

        windows = [win for win in gw.getWindowsWithTitle('') if win.title not in ["", "Settings", "Select Window", "Windows Input Experience", "Program Manager"]]
        
        max_columns = 4
        for index, window in enumerate(windows):
            img = self.get_window_preview(window)
            if not img:
                img = self.get_window_icon(window)
             
            widgets_frame = ttk.Frame(window_list_frame, padding=(0, 0, 0, 10))
            widgets_frame.columnconfigure(index=0, weight=1)
            if self.is_image_black(img):
                img = self.get_window_icon(window)
            
            self.preview_images.append(img)
            photo = ImageTk.PhotoImage(img)
            btn = tk.Button(widgets_frame, image=photo, command=lambda w=window: self.app.start_translation(w))
            btn.image = photo
            row = index // max_columns
            column = index % max_columns

            title = window.title if len(window.title) <= 30 else window.title[:30] + '...'
            label = tk.Label(widgets_frame, text=title)
            btn.grid(row=0, column=column, padx=10, pady=0)
            label.grid(row=1, column=column)
            widgets_frame.grid(row=row, column=column, pady=10)

        # Enable scrolling with mouse wheel and trackpad gestures
        window_list_frame.bind("<Enter>", lambda e: self._bind_to_mousewheel(e, canvas))
        window_list_frame.bind("<Leave>", lambda e: self._unbind_from_mousewheel(e, canvas))

    def get_window_preview(self, window):
        left, top, right, bot = win32gui.GetWindowRect(window._hWnd)
        width, height = right - left, bot - top

        hwndDC = win32gui.GetWindowDC(window._hWnd)
        mfcDC = win32ui.CreateDCFromHandle(hwndDC)
        saveDC = mfcDC.CreateCompatibleDC()

        saveBitMap = win32ui.CreateBitmap()
        saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
        saveDC.SelectObject(saveBitMap)
        saveDC.BitBlt((0, 0), (width, height), mfcDC, (0, 0), win32con.SRCCOPY)

        bmpinfo = saveBitMap.GetInfo()
        bmpstr = saveBitMap.GetBitmapBits(True)
        img = Image.frombuffer('RGB', (bmpinfo['bmWidth'], bmpinfo['bmHeight']), bmpstr, 'raw', 'BGRX', 0, 1)
        
        win32gui.DeleteObject(saveBitMap.GetHandle())
        saveDC.DeleteDC()
        mfcDC.DeleteDC()
        win32gui.ReleaseDC(window._hWnd, hwndDC)
        
        img = img.resize((240, 135), Image.Resampling.LANCZOS)
        return img

    def is_image_black(self, img):
        return all(pixel == (0, 0, 0) for pixel in img.getdata())

    def get_window_icon(self, window):
        _, icon_small = win32gui.SendMessageTimeout(
            window._hWnd, win32con.WM_GETICON, win32con.ICON_SMALL, 0, win32con.SMTO_ABORTIFHUNG, 200)
        if icon_small == 0:
            icon_small = win32gui.GetClassLong(window._hWnd, win32con.GCL_HICON)
        if icon_small != 0:
            hdc = win32ui.CreateDCFromHandle(win32gui.GetDC(0))
            hdc_mem = hdc.CreateCompatibleDC()
            bmp = win32ui.CreateBitmap()
            bmp.CreateCompatibleBitmap(hdc, 240, 135)
            hdc_mem.SelectObject(bmp)
            hdc_mem.DrawIcon((0, 0), win32gui.CopyIcon(icon_small))
            icon_img = Image.frombuffer(
                "RGB", (16, 16), bmp.GetBitmapBits(True), "raw", "BGRX", 0, 1)
            # win32gui.DestroyIcon(icon_small)
            img = icon_img.resize((240, 135), Image.Resampling.LANCZOS)
            return img
        return Image.new("RGB", (240, 135), color="black")

    def _bind_to_mousewheel(self, event,canvas):
        canvas.bind_all("<MouseWheel>", lambda e : self._on_mousewheel(e, canvas))

    def _unbind_from_mousewheel(self, event, canvas):
        canvas.unbind_all("<MouseWheel>")

    def _on_mousewheel(self, event, canvas):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
