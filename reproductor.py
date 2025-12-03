import tkinter as tk
from tkinter import filedialog
import pyaudio
import wave
import threading
import utils
import time
import vlc
import re
from pathlib import Path

# --- COLORES ---
DARK_BG = "#1e1e1e"
DARKER_BG = "#121212"
ACCENT_COLOR = "#71f099"
TEXT_COLOR = "#ffffff"
BUTTON_BG = "#2d2d2d"
BUTTON_HOVER = "#3d3d3d"

# --- TEMAS ---
THEMES = {
    "dark": {
        "bg": "#1e1e1e",
        "darker_bg": "#121212",
        "accent": "#71f099",
        "fg": "#ffffff",
        "button_bg": "#2d2d2d",
        "button_fg": "#ffffff",
        "button_active_fg": "#121212",
        "button_hover": "#3d3d3d"
    },
    "light": {
        "bg": "#f3f3f3",
        "darker_bg": "#ffffff",
        "accent": "#71f099",
        "fg": "#000000",
        "button_bg": "#e0e0e0",
        "button_fg": "#000000",
        "button_active_fg": "#ffffff",
        "button_hover": "#d0d0d0"
    }
}

CURRENT_THEME = "dark"

def applyTheme(win, theme):
    try:
        win.configure(bg=theme["bg"])
    except Exception:
        pass

    for child in win.winfo_children():
        cls = child.__class__.__name__
        if cls in ("Frame", "Labelframe"):
            try:
                child.config(bg=theme["bg"])
            except Exception:
                pass
        elif cls == "Label":
            try:
                child.config(bg=theme["bg"], fg=theme["fg"])
            except Exception:
                pass
        elif cls == "Button":
            try:
                child.config(bg=theme["button_bg"], fg=theme["button_fg"],
                             activebackground=theme["accent"], activeforeground=theme["button_active_fg"])
            except Exception:
                pass
        elif cls == "Scale":
            try:
                child.config(bg=theme["button_bg"], fg=theme["accent"], troughcolor=theme["darker_bg"])
            except Exception:
                pass
        try:
            if child.winfo_children():
                applyTheme(child, theme)
        except Exception:
            pass
        
# --- FUNCIONES DE SUBTÍTULOS ---
def parseSRT(filePath):
    subtitles = []
    try:
        with open(filePath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        blocks = content.strip().split('\n\n')
        for block in blocks:
            lines = block.strip().split('\n')
            if len(lines) < 3:
                continue
            
            timecode = lines[1]
            match = re.match(r'(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2}),(\d{3})', timecode)
            if not match:
                continue
            
            h1, m1, s1, ms1, h2, m2, s2, ms2 = map(int, match.groups())
            start_ms = (h1 * 3600 + m1 * 60 + s1) * 1000 + ms1
            end_ms = (h2 * 3600 + m2 * 60 + s2) * 1000 + ms2
            text = '\n'.join(lines[2:])
            
            subtitles.append((start_ms, end_ms, text))
    except Exception as e:
        print(f"Error parsing SRT: {e}")
    
    return subtitles

# --- REPRODUCTOR DE AUDIO ---
class musicPlayer:
    def __init__(self, master):
        self.master = master
        self.master.title("Reproductor de música")
        self.master.configure(bg=DARK_BG)
        self.centerWindow(600, 220)

        # --- FRAME (CONTENEDOR) PRINCIPAL DE CONTROLES ---
        controlsFrame = tk.Frame(master, bg=DARK_BG)
        controlsFrame.pack(pady=15)

        self.playButton = tk.Button(controlsFrame, text="▶ Reproducir", width=12, command=self.playAudio, 
                                     state="disabled", bg=BUTTON_BG, fg=TEXT_COLOR, activebackground=ACCENT_COLOR,
                                     activeforeground=DARKER_BG, relief="flat", font=("Segoe UI", 10, "bold"), padx=10, pady=8)
        self.playButton.grid(row=0, column=0, padx=8)

        self.pauseButton = tk.Button(controlsFrame, text="⏸ Pausar", width=12, command=self.pauseAudio, 
                                      state="disabled", bg=BUTTON_BG, fg=TEXT_COLOR, activebackground=ACCENT_COLOR,
                                      activeforeground=DARKER_BG, relief="flat", font=("Segoe UI", 10, "bold"), padx=10, pady=8)
        self.pauseButton.grid(row=0, column=1, padx=8)

        self.stopButton = tk.Button(controlsFrame, text="⏹ Detener", width=12, command=self.stopAudio, 
                                     state="disabled", bg=BUTTON_BG, fg=TEXT_COLOR, activebackground=ACCENT_COLOR,
                                     activeforeground=DARKER_BG, relief="flat", font=("Segoe UI", 10, "bold"), padx=10, pady=8)
        self.stopButton.grid(row=0, column=2, padx=8)

        self.loadButton = tk.Button(controlsFrame, text="📂 Cargar Audio", width=15, command=self.loadFile,
                                     bg=ACCENT_COLOR, fg=DARKER_BG, relief="flat", font=("Segoe UI", 10, "bold"), padx=10, pady=8)
        self.loadButton.grid(row=0, column=3, padx=8)

        # --- BARRA DE PROGRESO ---
        self.progress = tk.Scale(master, from_=0, to=1000, orient="horizontal", length=500, showvalue=0, 
                                 command=self.updatePos, bg=BUTTON_BG, fg=ACCENT_COLOR, 
                                 troughcolor=DARKER_BG, highlightthickness=0)
        self.progress.pack(pady=15, padx=30)

        # --- TIEMPOS ---
        self.timeFrame = tk.Frame(master, bg=DARK_BG)
        self.timeFrame.pack(fill="x", padx=30, pady=5)

        self.currentTimeLabel = tk.Label(self.timeFrame, text="0:00", bg=DARK_BG, fg=TEXT_COLOR, 
                                         font=("Segoe UI", 10))
        self.currentTimeLabel.pack(side="left")

        self.totalTimeLabel = tk.Label(self.timeFrame, text="0:00", bg=DARK_BG, fg=TEXT_COLOR, 
                                       font=("Segoe UI", 10))
        self.totalTimeLabel.pack(side="right")

        # --- "REPRODUCIENDO AHORA" ---
        self.nowPlayingLabel = tk.Label(master, text="", font=("Segoe UI", 11, "italic"), 
                                         fg=ACCENT_COLOR, bg=DARK_BG)
        self.nowPlayingLabel.pack(pady=10)

        # --- VARIABLES INTERNAS ---
        self.audioThread = None
        self.isPlaying = False
        self.isPaused = False
        self.audioFile = None
        self.currentPos = 0
        self.totalFrames = 0
        self.frameRate = 0
        self.duration = 0
        self.sliderChange = None
        self.updatingProgress = False

    # --- MÉTODOS ---
    # Cargar archivo de audio
    def loadFile(self):
        filePath = filedialog.askopenfilename(filetypes=[("Archivos de audio/video", "*.mp3 *.wav *.flac *.ogg *.m4a *.aac *.mp4 *.mkv")])
        if not filePath:
            return
        self.audioFile = filePath
        media = vlc.Media(filePath)
        self.player.set_media(media)

        length = self.player.get_length()
        if length <= 0:
            self.player.play()
            time.sleep(0.2)
            self.player.pause()
            length = self.player.get_length()

        total_secs = max(0, length // 1000)
        self.progress.config(from_=0, to=1000)
        self.progress.set(0)
        self.totalTimeLabel.config(text=self._formatTime(total_secs))
        self.currentTimeLabel.config(text="0:00")
        self.nowPlayingLabel.config(text="Archivo cargado: " + self.audioFile.split('/')[-1])

        self.playButton.config(state="normal")
        self.stopButton.config(state="disabled")
        self.pauseButton.config(state="disabled")

    # Reproducir audio
    def playAudio(self):
        if not self.audioFile:
            return
        self.player.play()
        self.isPlaying = True
        self.isPaused = False
        self.playButton.config(state="disabled")
        self.pauseButton.config(state="normal")
        self.stopButton.config(state="normal")

        if not self.updateThread or not self.updateThread.is_alive():
            self.updateThread = threading.Thread(target=self._updateSlider, daemon=True)
            self.updateThread.start()

    # Pausar audio
    def pauseAudio(self):
        if not self.isPlaying:
            return
        self.player.pause()
        self.isPaused = not self.isPaused
        self.pauseButton.config(text="▶ Reanudar" if self.isPaused else "⏸ Pausar")

    # Método para detener la reproducción
    def stopAudio(self):
        self.player.stop()
        self.isPlaying = False
        self.isPaused = False
        self.progress.set(0)
        self.currentTimeLabel.config(text="0:00")
        self.totalTimeLabel.config(text="0:00")
        self.nowPlayingLabel.config(text="")
        self.playButton.config(state="normal")
        self.pauseButton.config(state="disabled", text="⏸ Pausar")
        self.stopButton.config(state="disabled")
        self.updatingProgress = False

    # Método para controlar la reproducción del audio
    def _playAudio(self):
        chunk = 1024
        waveFile = wave.open(self.audioFile, 'rb')
        pAud = pyaudio.PyAudio()

        # Configuración del audio
        stream = pAud.open(format=pAud.get_format_from_width(waveFile.getsampwidth()),
                           channels=waveFile.getnchannels(),
                           rate=waveFile.getframerate(),
                           output=True)
        
        # Posicionar en el frame correcto si se movió el slider
        if self.sliderChange is not None:
            newFrame = int(self.sliderChange * self.frameRate)
            waveFile.setpos(newFrame)
            self.currentPos = newFrame
            self.sliderChange = None
        else:
            self.currentPos = 0
        # Leer datos
        data = waveFile.readframes(chunk)
        threading.Thread(target=self._updateSlider, daemon=True).start()

        while data and self.isPlaying:
            if self.isPaused:
                time.sleep(0.1)
                continue

            if self.sliderChange is not None:
                newFrame = int(self.sliderChange * self.frameRate)
                waveFile.setpos(newFrame)
                self.currentPos = newFrame
                self.sliderChange = None
                data = waveFile.readframes(chunk)
                continue

            stream.write(data)
            self.currentPos = waveFile.tell()
            data = waveFile.readframes(chunk)

        stream.stop_stream()
        stream.close()
        pAud.terminate()
        waveFile.close()
        self.isPlaying = False
        self.updatingProgress = False
        self.progress.set(0)
        self.currentTimeLabel.config(text="0:00")
        self.nowPlayingLabel.config(text="")
        self.playButton.config(state="normal")
        self.pauseButton.config(state="disabled", text="⏸ Pausar")
        self.stopButton.config(state="disabled")
        
    # Método para actualizar el slider
    def _updateSlider(self):
        self.updatingProgress = True
        while self.isPlaying and self.updatingProgress:
            if not self.isPaused:
                currentTime = self.currentPos / self.frameRate
                self.progress.set(currentTime)
                self.currentTimeLabel.config(text=self._formatTime(currentTime))
            time.sleep(0.2)
        self.updatingProgress = False
    # Método para darle formato correcto al tiempo
    def _formatTime(self, seconds):
        m = int(seconds // 60)
        s = int(seconds % 60)
        return f"{m}:{s:02}"
    # Método para actualizar la posición del audio al mover el slider
    def updatePos(self, value):
        if not self.audioFile:
            return
        seconds = float(value)
        if self.isPlaying:
            self.sliderChange = seconds
        else:
            self.progress.set(seconds)
            self.currentTimeLabel.config(text=self._formatTime(seconds))
    # Método para centrar la ventana
    def centerWindow(self, width, height):
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.master.geometry(f"{width}x{height}+{x}+{y}")

# --- REPRODUCTOR DE VIDEO ---
class videoPlayer:
    def __init__(self, master):
        self.master = master
        self.master.title("Reproductor de Video")
        self.master.configure(bg=DARK_BG)
        self.center_window(900, 600)

        # Use MediaListPlayer instead of MediaPlayer for subtitle support
        self.instance = vlc.Instance()
        self.mediaList = self.instance.media_list_new()
        self.player = self.instance.media_list_player_new()

        # --- CONTROLES ---
        controlsFrame = tk.Frame(master, bg=DARK_BG)
        controlsFrame.pack(pady=12)

        self.playButton = tk.Button(controlsFrame, text="▶ Reproducir", width=12, command=self.playVideo, 
                                     state="disabled", bg=BUTTON_BG, fg=TEXT_COLOR, activebackground=ACCENT_COLOR,
                                     activeforeground=DARKER_BG, relief="flat", font=("Segoe UI", 10, "bold"), padx=10, pady=8)
        self.playButton.grid(row=0, column=0, padx=8)
        
        self.pauseButton = tk.Button(controlsFrame, text="⏸ Pausar", width=12, command=self.pauseVideo, 
                                      state="disabled", bg=BUTTON_BG, fg=TEXT_COLOR, activebackground=ACCENT_COLOR,
                                      activeforeground=DARKER_BG, relief="flat", font=("Segoe UI", 10, "bold"), padx=10, pady=8)
        self.pauseButton.grid(row=0, column=1, padx=8)
        
        self.stopButton = tk.Button(controlsFrame, text="⏹ Detener", width=12, command=self.stopVideo, 
                                     state="disabled", bg=BUTTON_BG, fg=TEXT_COLOR, activebackground=ACCENT_COLOR,
                                     activeforeground=DARKER_BG, relief="flat", font=("Segoe UI", 10, "bold"), padx=10, pady=8)
        self.stopButton.grid(row=0, column=2, padx=8)
        
        self.loadButton = tk.Button(controlsFrame, text="📂 Cargar Video", width=15, command=self.loadFile,
                                     bg=ACCENT_COLOR, fg=DARKER_BG, relief="flat", font=("Segoe UI", 10, "bold"), padx=10, pady=8)
        self.loadButton.grid(row=0, column=3, padx=8)

        self.loadSubtitleButton = tk.Button(controlsFrame, text="💬 Cargar Subtítulos", width=15,
                                    command=self.loadSubtitle,
                                    bg=ACCENT_COLOR, fg=DARKER_BG, relief="flat",
                                    font=("Segoe UI", 10, "bold"), padx=10, pady=8)
        self.loadSubtitleButton.grid(row=0, column=4, padx=8)

        # --- FRAME DE VIDEO ---
        self.videoFrame = tk.Frame(master, bg=DARKER_BG, width=640, height=360)
        self.videoFrame.pack(pady=12, padx=20, fill="both", expand=True)

        # --- OVERLAY DE SUBTÍTULOS ---
        self.subtitle_overlay = tk.Toplevel(self.master)
        self.subtitle_overlay.overrideredirect(True)
        self.subtitle_overlay.attributes("-topmost", True)
        self.subtitle_overlay.configure(bg="magenta")
        try:
            self.subtitle_overlay.wm_attributes("-transparentcolor", "magenta")
        except Exception:
            pass
        self.subtitle_overlay_label = tk.Label(self.subtitle_overlay, text="", font=("Segoe UI", 14, "bold"),
                                               bg="magenta", fg="#FFFF00", wraplength=600, justify="center")
        self.subtitle_overlay_label.pack(expand=True, fill="both")
        self.subtitle_overlay.withdraw()

        # --- BARRA DE PROGRESO ---
        self.progress = tk.Scale(master, from_=0, to=0, orient="horizontal", length=600,
                                 showvalue=0, command=self.updatePos, bg=BUTTON_BG, fg=ACCENT_COLOR,
                                 troughcolor=DARKER_BG, highlightthickness=0)
        self.progress.pack(pady=10, padx=30)

        timeFrame = tk.Frame(master, bg=DARK_BG)
        timeFrame.pack(fill="x", padx=30, pady=5)

        self.currentTimeLabel = tk.Label(timeFrame, text="0:00", bg=DARK_BG, fg=TEXT_COLOR, 
                                         font=("Segoe UI", 10))
        self.currentTimeLabel.pack(side="left")
        
        self.totalTimeLabel = tk.Label(timeFrame, text="0:00", bg=DARK_BG, fg=TEXT_COLOR, 
                                       font=("Segoe UI", 10))
        self.totalTimeLabel.pack(side="right")

        self.nowPlayingLabel = tk.Label(master, text="", font=("Segoe UI", 11, "italic"), 
                                         fg=ACCENT_COLOR, bg=DARK_BG)
        self.nowPlayingLabel.pack(pady=8)

        # --- VARIABLES ---
        self.videoFile = None
        self.subtitleFile = None
        self.subtitles = []
        self.isPlaying = False
        self.isPaused = False
        self.sliderChange = None
        self.updatingProgress = False
        self.updateThread = None

    # --- MÉTODOS ---
    def center_window(self, width, height):
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.master.geometry(f"{width}x{height}+{x}+{y}")

    # Cargar subtítulos
    def loadSubtitle(self):
        if not self.videoFile:
            return
        subtitlePath = filedialog.askopenfilename(filetypes=[("Archivos de subtítulos", "*.srt *.sub *.ass *.ssa")])
        if subtitlePath:
            self.subtitleFile = subtitlePath
            self.subtitles = parseSRT(subtitlePath)
            mediaPlayer = self.player.get_media_player()
            if mediaPlayer:
                try:
                    mediaPlayer.video_set_subtitle_file(subtitlePath)
                    self.nowPlayingLabel.config(text="Subtítulos cargados: " + subtitlePath.split('/')[-1])
                except Exception as e:
                    print(f"Error loading subtitles: {e}")

            self.subtitle_overlay.deiconify()

     
    # Cargar archivo de video
    def loadFile(self):
        filePath = filedialog.askopenfilename(filetypes=[("Archivos de video", "*.mp4 *.avi *.mkv *.mov *.flv *.wmv")])
        if filePath:
            self.videoFile = filePath
            self.subtitleFile = None
            self.subtitles = []
            
            self.mediaList = self.instance.media_list_new()
            media = self.instance.media_new(filePath)
            self.mediaList.add_media(media)
            self.player.set_media_list(self.mediaList)
            
            mediaPlayer = self.player.get_media_player()
            mediaPlayer.set_hwnd(self.videoFrame.winfo_id())

            self.posSub()
            self.subtitle_overlay.deiconify()

            self.playButton.config(state="normal")
            self.stopButton.config(state="disabled")
            self.pauseButton.config(state="disabled")
            self.nowPlayingLabel.config(text="Archivo cargado: " + self.videoFile.split('/')[-1])

    # Reproducir video
    def playVideo(self):
        if not self.videoFile:
            return
        self.player.play()
        self.isPlaying = True
        self.isPaused = False

        self.playButton.config(state="disabled")
        self.pauseButton.config(state="normal")
        self.stopButton.config(state="normal")

        # Hilo para actualizar slider
        if not self.updateThread or not self.updateThread.is_alive():
            self.updateThread = threading.Thread(target=self.updateSlider, daemon=True)
            self.updateThread.start()

    # Pausar video
    def pauseVideo(self):
        if not self.isPlaying:
            return
        self.player.pause()
        self.isPaused = not self.isPaused
        if self.isPaused:
            self.pauseButton.config(text="▶ Reanudar")
        else:
            self.pauseButton.config(text="⏸ Pausar")

    # Detener video
    def stopVideo(self):
        self.player.stop()
        self.isPlaying = False
        self.isPaused = False
        self.progress.set(0)
        self.currentTimeLabel.config(text="0:00")
        self.totalTimeLabel.config(text="0:00")
        self.nowPlayingLabel.config(text="")
        self.subtitle_overlay_label.config(text="")
        self.subtitle_overlay.withdraw()
        self.playButton.config(state="normal")
        self.pauseButton.config(state="disabled", text="⏸ Pausar")
        self.stopButton.config(state="disabled")

    # Mover slider
    def updatePos(self, value):
        if not self.videoFile:
            return
        pos = float(value) / 1000
        if self.isPlaying:
            mediaPlayer = self.player.get_media_player()
            mediaPlayer.set_position(pos)
        else:
            self.progress.set(float(value))
            mediaPlayer = self.player.get_media_player()
            length = mediaPlayer.get_length() // 1000
            current = int(pos * length)
            self.currentTimeLabel.config(text=self.formatTime(current))

    # Hilo para actualizar slider y tiempo
    def updateSlider(self):
        self.updatingProgress = True
        while self.isPlaying and self.updatingProgress:
            if not self.isPaused:
                mediaPlayer = self.player.get_media_player()
                length = mediaPlayer.get_length()
                if length > 0:
                    time_ms = mediaPlayer.get_time()
                    pos = time_ms / length
                    self.progress.config(to=1000)
                    self.progress.set(pos * 1000)
                    current = time_ms // 1000
                    total = length // 1000
                    self.currentTimeLabel.config(text=self.formatTime(current))
                    self.totalTimeLabel.config(text=self.formatTime(total))
                    self.posSub()
                    self.updateSub(time_ms)
            time.sleep(0.2)

    def updateSub(self, time_ms):
        """Update subtitle label based on current playback time"""
        current_text = ""
        for start, end, text in self.subtitles:
            if start <= time_ms <= end:
                current_text = text
                break
        self.subtitle_overlay_label.config(text=current_text)

    def posSub(self):
        
        self.master.update_idletasks()
        x = self.videoFrame.winfo_rootx()
        y = self.videoFrame.winfo_rooty()
        w = max(100, self.videoFrame.winfo_width())
        h = max(50, self.videoFrame.winfo_height())
        overlay_h = max(40, int(h * 0.18))
        overlay_y = y + h - overlay_h - 8
        try:
            self.subtitle_overlay.geometry(f"{w}x{overlay_h}+{x}+{overlay_y}")
        except Exception:
            pass

    def formatTime(self, seconds):
        m = int(seconds // 60)
        s = int(seconds % 60)
        return f"{m}:{s:02}"

     
# --- MENÚ PRINCIPAL ---
class mainApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Reproductor Multimedia")
        self.master.configure(bg=DARK_BG)
        self.center_window(400, 400)
        
        self.themeButton = tk.Button(master, text="🌙", width=6, command=self.toggleTheme,
                                     bg=THEMES[CURRENT_THEME]["button_bg"], fg=THEMES[CURRENT_THEME]["button_fg"],
                                     activebackground=THEMES[CURRENT_THEME]["accent"], activeforeground=THEMES[CURRENT_THEME]["button_active_fg"],
                                     relief="flat", font=("Segoe UI", 10, "bold"))
        self.themeButton.pack(pady=(0,10))
        
        applyTheme(self.master, THEMES[CURRENT_THEME])

        titleLabel = tk.Label(master, text="Reproductor Multimedia", font=("Segoe UI", 18, "bold"),
                              fg=THEMES[CURRENT_THEME]["accent"], bg=DARK_BG)
        titleLabel.pack(pady=20)

        self.audioButton = tk.Button(master, text="♫ Reproductor de Audio", width=25, height=3, 
                                      command=self.openMusicPlayer, bg=BUTTON_BG, fg=TEXT_COLOR,
                                      activebackground=ACCENT_COLOR, activeforeground=DARKER_BG,
                                      relief="flat", font=("Segoe UI", 11, "bold"))
        self.audioButton.pack(pady=15, padx=30, fill="x")

        self.videoButton = tk.Button(master, text="🎬 Reproductor de Video", width=25, height=3, 
                                      command=self.openVideoPlayer, bg=BUTTON_BG, fg=TEXT_COLOR,
                                      activebackground=ACCENT_COLOR, activeforeground=DARKER_BG,
                                      relief="flat", font=("Segoe UI", 11, "bold"))
        self.videoButton.pack(pady=15, padx=30, fill="x")

    # Cambiar tema
    def toggleTheme(self):
        global CURRENT_THEME
        CURRENT_THEME = "light" if CURRENT_THEME == "dark" else "dark"
        self.themeButton.config(text="🌙" if CURRENT_THEME == "dark" else "☀️")
        applyTheme(self.master, THEMES[CURRENT_THEME])
        try:
            if hasattr(self, "newWindow") and self.newWindow.winfo_exists():
                applyTheme(self.newWindow, THEMES[CURRENT_THEME])
        except Exception:
            pass

    def openMusicPlayer(self):
        self.newWindow = tk.Toplevel(self.master)
        self.app = musicPlayer(self.newWindow)
       

    def openVideoPlayer(self):
        self.newWindow = tk.Toplevel(self.master)
        self.app = videoPlayer(self.newWindow)
       

    def center_window(self, width, height):
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.master.geometry(f"{width}x{height}+{x}+{y}")
        
if __name__ == "__main__":
    root = tk.Tk()
    app = mainApp(root)
    root.mainloop()
