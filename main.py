import customtkinter as ctk
import requests
import json
import io
from PIL import Image
import os
import sys

# Paths
if getattr(sys, "frozen", False):
    BASE_PATH = sys._MEIPASS
else:
    BASE_PATH = os.path.dirname(__file__)

REMOTE_JSON_URL = "https://raw.githubusercontent.com/Nugetinc/SwitchDownloader/refs/heads/main/apps.json"
DOWNLOAD_DIR = os.path.join(BASE_PATH, "downloads")

class MarketplaceApp(ctk.CTk):
    # Display sizes
    COVER_DISPLAY_SIZE = (200, 300)
    BANNER_DISPLAY_SIZE = (600, 338)

    # HD sizes
    COVER_HD_SIZE = (600, 900)
    BANNER_HD_SIZE = (1920, 1080)

    def __init__(self):
        super().__init__()
        self.title("SwitchDownloader")
        self.state("zoomed")  # Start maximized
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        os.makedirs(DOWNLOAD_DIR, exist_ok=True)

        self.data = {}
        self.categories = {}
        self.images = []  # keep references to CTkImage

        # Topbar for categories
        self.topbar = ctk.CTkFrame(self, height=60)
        self.topbar.pack(side="top", fill="x", padx=5, pady=5)

        self.category_frame = ctk.CTkScrollableFrame(self.topbar, height=50)
        self.category_frame.pack(side="left", fill="x", expand=True, padx=10, pady=5)

        # Grid for apps
        self.grid_frame = ctk.CTkScrollableFrame(self)
        self.grid_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.load_store()

    def load_store(self):
        try:
            if REMOTE_JSON_URL.startswith("http"):
                r = requests.get(REMOTE_JSON_URL)
                r.raise_for_status()
                self.data = r.json()
            else:
                with open(REMOTE_JSON_URL, "r", encoding="utf-8") as f:
                    self.data = json.load(f)

            self.categories = self.data.get("categories", {})
            self.build_category_buttons()

            if self.categories:
                first_cat = list(self.categories.keys())[0]
                self.show_category(first_cat)

        except Exception as e:
            ctk.CTkLabel(self.grid_frame, text=f"Failed to load store: {e}", text_color="red").grid(row=0, column=0, pady=50)

    def build_category_buttons(self):
        for widget in self.category_frame.winfo_children():
            widget.destroy()

        for category in self.categories:
            btn = ctk.CTkButton(
                self.category_frame, text=category, width=120,
                command=lambda c=category: self.show_category(c)
            )
            btn.pack(side="left", padx=5)

    def show_category(self, category):
        for widget in self.grid_frame.winfo_children():
            widget.destroy()

        apps = self.categories.get(category, [])
        if not apps:
            ctk.CTkLabel(self.grid_frame, text="No apps in this category yet.", font=("Arial", 16)).grid(row=0, column=0, pady=50)
            return

        row, col = 0, 0
        for app in apps:
            self.add_cover_tile(app, row, col)
            col += 1
            if col >= 4:
                col = 0
                row += 1

    def add_cover_tile(self, app, row, col):
        frame = ctk.CTkFrame(self.grid_frame, corner_radius=12)
        frame.grid(row=row, column=col, padx=10, pady=10)

        cover_img = None
        cover_url = app.get("cover_url", "")
        try:
            if cover_url:
                if cover_url.startswith("http"):
                    img_data = requests.get(cover_url).content
                    pil_img = Image.open(io.BytesIO(img_data))
                else:
                    pil_img = Image.open(cover_url)
                pil_img = pil_img.resize(self.COVER_HD_SIZE)
                cover_img = ctk.CTkImage(light_image=pil_img, size=self.COVER_DISPLAY_SIZE)
                self.images.append(cover_img)
        except Exception as e:
            print(f"Failed to load cover: {e}")

        if cover_img is None:
            pil_placeholder = Image.new("RGB", self.COVER_HD_SIZE, color=(50,50,50))
            cover_img = ctk.CTkImage(light_image=pil_placeholder, size=self.COVER_DISPLAY_SIZE)
            self.images.append(cover_img)

        btn = ctk.CTkButton(
            frame, text="", image=cover_img,
            width=self.COVER_DISPLAY_SIZE[0], height=self.COVER_DISPLAY_SIZE[1],
            fg_color="transparent", hover_color="gray20",
            command=lambda: self.open_detail_window(app)
        )
        btn.pack()

    def open_detail_window(self, app):
        detail_win = ctk.CTkToplevel(self)
        detail_win.title(app.get("name", "App Details"))
        detail_win.geometry("650x800")

        banner_url = app.get("banner_url") or app.get("cover_url")
        banner_img = None
        if banner_url:
            try:
                if banner_url.startswith("http"):
                    img_data = requests.get(banner_url).content
                    pil_img = Image.open(io.BytesIO(img_data))
                else:
                    pil_img = Image.open(banner_url)
                pil_img = pil_img.resize(self.BANNER_HD_SIZE)
                banner_img = ctk.CTkImage(light_image=pil_img, size=self.BANNER_DISPLAY_SIZE)
                self.images.append(banner_img)
                ctk.CTkLabel(detail_win, image=banner_img, text="").pack(pady=10)
            except Exception as e:
                print(f"Failed to load banner: {e}")
                ctk.CTkLabel(detail_win, text="[No Banner]").pack(pady=10)
        else:
            ctk.CTkLabel(detail_win, text="[No Banner]").pack(pady=10)

        ctk.CTkLabel(detail_win, text=app.get("name", "Unnamed App"), font=("Arial", 20, "bold")).pack(pady=(0,5))
        ctk.CTkLabel(detail_win, text=app.get("description", ""), wraplength=600, justify="left").pack(pady=(0,5))
        ctk.CTkLabel(detail_win, text=f"Version: {app.get('version', '?')} | By: {app.get('author', 'Unknown')}", text_color="gray").pack(pady=(0,10))
        ctk.CTkButton(detail_win, text="Download", command=lambda: self.download_app(app)).pack(pady=15)

    def download_app(self, app):
        name = app.get("name", "Unknown")
        url = app.get("download_url", "").strip()
        if not url or url.lower() in ["na", "n/a"]:
            ctk.CTkLabel(self.grid_frame, text=f"{name} has no valid download URL!", text_color="red").grid(pady=5)
            return

        try:
            r = requests.get(url)
            r.raise_for_status()
            file_ext = os.path.splitext(url)[-1] or ".zip"
            filename = os.path.join(DOWNLOAD_DIR, f"{name}{file_ext}")
            with open(filename, "wb") as f:
                f.write(r.content)
            ctk.CTkLabel(self.grid_frame, text=f"Downloaded {name}!", text_color="green").grid(pady=5)
        except Exception as e:
            ctk.CTkLabel(self.grid_frame, text=f"Failed to download {name}: {e}", text_color="red").grid(pady=5)

if __name__ == "__main__":
    app = MarketplaceApp()
    app.mainloop()
