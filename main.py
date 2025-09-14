import customtkinter as ctk
import requests
import json
import os

# -----------------------------
# CONFIG
# -----------------------------
REMOTE_JSON_URL = "apps.json"  # <-- replace with your real URL
DOWNLOAD_DIR = "downloads"

# -----------------------------
# APP CLASS
# -----------------------------
class MarketplaceApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Switch Marketplace")
        self.geometry("900x600")
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        # Create download folder if not exists
        os.makedirs(DOWNLOAD_DIR, exist_ok=True)

        # UI layout: sidebar + main area
        self.sidebar = ctk.CTkFrame(self, width=200)
        self.sidebar.pack(side="left", fill="y", padx=5, pady=5)

        self.main_frame = ctk.CTkScrollableFrame(self)
        self.main_frame.pack(side="right", fill="both", expand=True, padx=5, pady=5)

        self.categories = {}
        self.data = {}
        self.load_store()

    def load_store(self):
        try:
            response = requests.get(REMOTE_JSON_URL)
            response.raise_for_status()
            self.data = response.json()
            self.categories = self.data.get("categories", {})
            self.build_sidebar()
        except Exception as e:
            ctk.CTkLabel(self.main_frame, text=f"Failed to load store: {e}", text_color="red").pack()

    def build_sidebar(self):
        ctk.CTkLabel(self.sidebar, text="Categories", font=("Arial", 18, "bold")).pack(pady=10)
        for category in self.categories:
            btn = ctk.CTkButton(self.sidebar, text=category, command=lambda c=category: self.show_category(c))
            btn.pack(pady=5, fill="x")

    def show_category(self, category):
        # Clear current frame
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        apps = self.categories.get(category, [])
        if not apps:
            ctk.CTkLabel(self.main_frame, text="No apps here yet!").pack()
            return

        for app in apps:
            self.add_app_card(app)

    def add_app_card(self, app):
        frame = ctk.CTkFrame(self.main_frame)
        frame.pack(fill="x", padx=5, pady=5)

        name = app.get("name", "Unnamed App")
        desc = app.get("description", "")
        version = app.get("version", "")
        url = app.get("download_url", "")

        ctk.CTkLabel(frame, text=f"{name} (v{version})", font=("Arial", 16, "bold")).pack(anchor="w", padx=10, pady=2)
        ctk.CTkLabel(frame, text=desc, wraplength=500, justify="left").pack(anchor="w", padx=10)
        ctk.CTkButton(frame, text="Download", command=lambda: self.download_app(name, url)).pack(anchor="e", padx=10, pady=5)

    def download_app(self, name, url):
        if not url:
            ctk.CTkLabel(self.main_frame, text=f"⚠ No download URL for {name}", text_color="red").pack()
            return

        try:
            r = requests.get(url)
            r.raise_for_status()
            filename = os.path.join(DOWNLOAD_DIR, f"{name}.zip")
            with open(filename, "wb") as f:
                f.write(r.content)
            ctk.CTkLabel(self.main_frame, text=f"✅ Downloaded {name}!", text_color="green").pack()
        except Exception as e:
            ctk.CTkLabel(self.main_frame, text=f"❌ Failed to download {name}: {e}", text_color="red").pack()

# -----------------------------
# RUN APP
# -----------------------------
if __name__ == "__main__":
    app = MarketplaceApp()
    app.mainloop()
