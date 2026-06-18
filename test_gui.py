import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
import os
from downloader import Downloader

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

ACCENT = "#6C5CE7"
ACCENT_HOVER = "#7D6FF0"
BG_DARK = "#0D0D12"
BG_CARD = "#16161E"
BG_INPUT = "#1C1C26"
TEXT_SECONDARY = "#7A7A8A"
TEXT_MUTED = "#555566"

class ModernEntry(ctk.CTkEntry):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class QualityCard(ctk.CTkFrame):
    def __init__(self, master, text, value, variable, **kwargs):
        super().__init__(master, fg_color=BG_CARD, corner_radius=12, border_width=1.5, border_color="#222233", **kwargs)
        self.value = value
        self.var = variable
        self.label = ctk.CTkLabel(self, text=text, font=ctk.CTkFont(size=12, weight="bold"), text_color=TEXT_SECONDARY)
        self.label.pack(expand=True)
        self.bind("<Button-1>", self.select)
        self.label.bind("<Button-1>", self.select)
        self._update_style()

    def select(self, event=None):
        self.var.set(self.value)
        self._update_style()
        self.event_generate("<<QualityChanged>>")

    def _update_style(self):
        if self.var.get() == self.value:
            self.configure(fg_color=BG_CARD, border_color=ACCENT)
            self.label.configure(text_color="#FFFFFF")
        else:
            self.configure(fg_color=BG_CARD, border_color="#222233")
            self.label.configure(text_color=TEXT_SECONDARY)

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Baixador de Links")
        self.geometry("380x640")
        self.resizable(False, False)

        self.output_path = os.path.join(os.path.expanduser("~"), "Downloads")
        self.downloader = Downloader(
            progress_callback=self.update_progress,
            status_callback=self.update_status
        )
        self._build_ui()

    def _build_ui(self):
        self.configure(fg_color=BG_DARK)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        main = ctk.CTkFrame(self, fg_color=BG_DARK, corner_radius=0)
        main.grid(row=0, column=0, sticky="nsew")
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(main, fg_color=BG_DARK, corner_radius=0, height=80)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)
        header.grid_columnconfigure(0, weight=1)

        icon_frame = ctk.CTkFrame(header, fg_color=ACCENT, corner_radius=16, width=44, height=44)
        icon_frame.place(relx=0.5, rely=0.35, anchor="center")
        ctk.CTkLabel(icon_frame, text="DL", font=ctk.CTkFont(size=16, weight="bold"), text_color="#FFFFFF").place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(header, text="Baixador de Links", font=ctk.CTkFont(size=17, weight="bold"), text_color="#FFFFFF").place(relx=0.5, rely=0.72, anchor="center")

        body = ctk.CTkFrame(main, fg_color=BG_DARK, corner_radius=0)
        body.grid(row=1, column=0, padx=20, pady=(10, 0), sticky="nsew")
        body.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(body, text="Link do video", font=ctk.CTkFont(size=12), text_color=TEXT_MUTED).pack(anchor="w", pady=(0, 4))

        self.url_entry = ModernEntry(
            body,
            placeholder_text="https://youtube.com/watch?v=...",
            height=48, corner_radius=14,
            fg_color=BG_INPUT, border_color="#252535",
            text_color="#FFFFFF", placeholder_text_color=TEXT_MUTED,
            font=ctk.CTkFont(size=13)
        )
        self.url_entry.pack(fill="x", pady=(0, 16))

        self.download_btn = ctk.CTkButton(
            body, text="Baixar agora", height=50, corner_radius=14,
            fg_color=ACCENT, hover_color=ACCENT_HOVER,
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self.start_download
        )
        self.download_btn.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(body, text="Formato", font=ctk.CTkFont(size=12), text_color=TEXT_MUTED).pack(anchor="w", pady=(0, 6))

        fmt_frame = ctk.CTkFrame(body, fg_color=BG_DARK)
        fmt_frame.pack(fill="x", pady=(0, 16))
        fmt_frame.grid_columnconfigure((0,1), weight=1)

        self.fmt_var = ctk.StringVar(value="MP4")
        self.mp4_btn = ctk.CTkButton(
            fmt_frame, text="MP4", height=40, corner_radius=10,
            fg_color=ACCENT, hover_color=ACCENT_HOVER,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=lambda: self.set_format("MP4")
        )
        self.mp4_btn.grid(row=0, column=0, padx=(0, 4), sticky="ew")

        self.mp3_btn = ctk.CTkButton(
            fmt_frame, text="MP3", height=40, corner_radius=10,
            fg_color=BG_INPUT, hover_color="#252538",
            font=ctk.CTkFont(size=13),
            text_color=TEXT_SECONDARY,
            command=lambda: self.set_format("MP3")
        )
        self.mp3_btn.grid(row=0, column=1, padx=(4, 0), sticky="ew")

        ctk.CTkLabel(body, text="Qualidade", font=ctk.CTkFont(size=12), text_color=TEXT_MUTED).pack(anchor="w", pady=(0, 8))

        self.qual_frame = ctk.CTkFrame(body, fg_color=BG_DARK)
        self.qual_frame.pack(fill="x", pady=(0, 20))
        self.qual_frame.grid_columnconfigure((0,1,2,3), weight=1, uniform="q")

        self.quality_var = ctk.StringVar(value="best")
        self.qual_cards = {}

        self.video_qualities = [("Melhor", "best"), ("1080p", "1080p"), ("720p", "720p"), ("480p", "480p")]
        self.audio_qualities = [("320kbps", "320kbps"), ("192kbps", "192kbps"), ("128kbps", "128kbps")]

        for i, (label, val) in enumerate(self.video_qualities):
            card = QualityCard(self.qual_frame, text=label, value=val, variable=self.quality_var)
            card.grid(row=0, column=i, padx=3, sticky="nsew")
            card.bind("<<QualityChanged>>", lambda e: self._sync_quality())
            self.qual_cards[val] = card

        self.qual_label_video = ctk.CTkLabel(self.qual_frame, text="")
        self.qual_label_video.grid(row=1, column=0, columnspan=4, pady=(6, 0))

        sep = ctk.CTkFrame(body, fg_color="#1A1A24", height=1, corner_radius=0)
        sep.pack(fill="x", pady=(0, 14))

        self.progress = ctk.CTkProgressBar(body, height=5, corner_radius=3, fg_color="#1E1E2A", progress_color=ACCENT)
        self.progress.pack(fill="x")
        self.progress.set(0)

        self.status_frame = ctk.CTkFrame(body, fg_color="transparent")
        self.status_frame.pack(fill="x", pady=(6, 0))
        self.status_frame.grid_columnconfigure(0, weight=1)

        self.status_icon = ctk.CTkLabel(self.status_frame, text="○", font=ctk.CTkFont(size=10), text_color=TEXT_MUTED)
        self.status_icon.grid(row=0, column=0, padx=(0, 6))

        self.status_label = ctk.CTkLabel(self.status_frame, text="Pronto para baixar", font=ctk.CTkFont(size=11), text_color=TEXT_MUTED)
        self.status_label.grid(row=0, column=1, sticky="w")

        bottom = ctk.CTkFrame(main, fg_color=BG_CARD, corner_radius=16, height=100)
        bottom.grid(row=2, column=0, padx=0, pady=(0, 0), sticky="sew")
        bottom.grid_propagate(False)
        bottom.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(bottom, text="Historico", font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT_SECONDARY).pack(anchor="w", padx=16, pady=(10, 4))

        self.log_box = ctk.CTkTextbox(
            bottom, height=56, corner_radius=10,
            fg_color=BG_DARK, border_color="#1A1A24", border_width=1,
            text_color="#808098", font=ctk.CTkFont(size=11),
            activate_scrollbars=False
        )
        self.log_box.pack(fill="x", padx=12, pady=(0, 10))

    def set_format(self, fmt):
        self.fmt_var.set(fmt)
        is_mp3 = fmt == "MP3"
        for btn, color, txtcolor, is_on in [
            (self.mp4_btn, ACCENT if not is_mp3 else BG_INPUT, "#FFFFFF" if not is_mp3 else TEXT_SECONDARY, not is_mp3),
            (self.mp3_btn, ACCENT if is_mp3 else BG_INPUT, "#FFFFFF" if is_mp3 else TEXT_SECONDARY, is_mp3)
        ]:
            btn.configure(fg_color=color, text_color=txtcolor)
            if is_on:
                btn.configure(font=ctk.CTkFont(size=13, weight="bold"))

        self.qual_frame.grid_columnconfigure((0,1,2,3), weight=1, uniform="q")

        for card in self.qual_cards.values():
            card.grid_forget()
            card.destroy()
        self.qual_cards.clear()

        qualities = self.audio_qualities if is_mp3 else self.video_qualities
        for i, (label, val) in enumerate(qualities):
            card = QualityCard(self.qual_frame, text=label, value=val, variable=self.quality_var)
            card.grid(row=0, column=i, padx=3, sticky="nsew")
            card.bind("<<QualityChanged>>", lambda e: self._sync_quality())
            self.qual_cards[val] = card

        if is_mp3:
            self.quality_var.set("320kbps")
            self.qual_label_video.configure(text="Qualidade do audio")
        else:
            self.quality_var.set("best")
            self.qual_label_video.configure(text="")

    def _sync_quality(self):
        self.set_format(self.fmt_var.get())

    def update_progress(self, v):
        self.progress.set(v / 100.0)

    def update_status(self, text):
        self.status_label.configure(text=text)
        self.status_icon.configure(text="●" if "conclu" in text.lower() or "baixando" in text.lower() else "○")

    def log(self, msg):
        self.log_box.insert("end", msg + "\n")
        self.log_box.see("end")

    def start_download(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Aviso", "Cole um link primeiro!")
            return

        self.download_btn.configure(state="disabled", text="Baixando...")
        self.progress.set(0)
        self.log_box.delete("1.0", "end")
        self.status_label.configure(text="Iniciando...")

        fmt = self.fmt_var.get()
        q = self.quality_var.get()
        if fmt == "MP3":
            fmt_str = "Melhor Áudio (MP3)"
            aq = q
        elif q == "best":
            fmt_str = "Melhor Vídeo (MP4)"
            aq = None
        else:
            fmt_str = f"Vídeo {q} (MP4)"
            aq = None

        thread = threading.Thread(target=self._download, args=(url, fmt_str, aq), daemon=True)
        thread.start()

    def _download(self, url, fmt_str, aq=None):
        try:
            ok, result, title = self.downloader.download(url, self.output_path, fmt_str, audio_quality=aq or "192kbps")
            if ok:
                self.after(0, self._success, result, title)
            else:
                self.after(0, self._error, result)
        except Exception as e:
            self.after(0, self._error, str(e))

    def _success(self, path, title):
        self.progress.set(1)
        self.status_label.configure(text="Download concluido!")
        self.status_icon.configure(text="✓", text_color="#00D68F")
        self.log(f"OK: {title}")
        self.log(f"Salvo em: {path}")
        self.download_btn.configure(state="normal", text="Baixar agora")

    def _error(self, err):
        self.progress.set(0)
        self.status_label.configure(text="Erro no download")
        self.status_icon.configure(text="!", text_color="#FF6B6B")
        self.log(f"Erro: {err}")
        self.download_btn.configure(state="normal", text="Baixar agora")

if __name__ == "__main__":
    App().mainloop()
