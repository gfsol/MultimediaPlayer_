import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
import tkinter.font as tkfont
import time
import threading
import vlc
import re

# --- COLORES BASE DEL TEMA OSCURO ---
DARK_BG = "#1e1e1e"
DARKER_BG = "#121212"
ACCENT_COLOR = "#71f099"
TEXT_COLOR = "#ffffff"
BUTTON_BG = "#2d2d2d"

# --- DEFINICIÓN DE TEMAS (CLARO / OSCURO) ---
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

FONT_FAMILY = "Onest"


# --- INICIALIZACIÓN DE ESTILOS ---
def init_styles(root):
    """
    Configura la fuente global de Tk (intentando usar Onest)
    y define el estilo moderno para los ttk.Scale (sliders).
    """
    global FONT_FAMILY

    families = set(tkfont.families())
    if FONT_FAMILY not in families:
        if "Segoe UI" in families:
            FONT_FAMILY = "Segoe UI"
        else:
            default = tkfont.nametofont("TkDefaultFont")
            FONT_FAMILY = default.cget("family")

    
    default_font = tkfont.nametofont("TkDefaultFont")
    default_font.configure(family=FONT_FAMILY, size=10)
    root.option_add("*Font", default_font)


    style = ttk.Style()
    try:
        style.theme_use("clam")
    except:
        pass

    style.configure(
        "Modern.Horizontal.TScale",
        troughcolor=DARKER_BG,    # color de la pista
        background=ACCENT_COLOR,  # color del thumb
        troughrelief="flat",
        borderwidth=0,
        sliderlength=18,
        sliderrelief="flat"
    )

    style.map(
        "Modern.Horizontal.TScale",
        background=[
            ("active", ACCENT_COLOR),
            ("!active", ACCENT_COLOR)
        ]
    )


# --- APLICAR TEMA A UNA VENTANA Y SUS PROCESOS HIJOS ---
def applyTheme(win, theme):
    try:
        win.configure(bg=theme["bg"])
    except:
        pass
    for child in win.winfo_children():
        cls = child.__class__.__name__
        if cls in ("Frame", "Labelframe"):
            try:
                child.config(bg=theme["bg"])
            except:
                pass
        elif cls == "Label":
            try:
                child.config(bg=theme["bg"], fg=theme["fg"])
            except:
                pass
        elif cls == "Button":
            try:
                child.config(bg=theme["button_bg"], fg=theme["button_fg"],
                             activebackground=theme["accent"],
                             activeforeground=theme["button_active_fg"])
            except:
                pass
        try:
            if child.winfo_children():
                applyTheme(child, theme)
        except:
            pass


# --- PARSEO DE SUBTÍTULOS SRT ---
def parseSRT(filePath):
    subtitles = []
    try:
        with open(filePath, 'r', encoding='utf-8') as f:
            content = f.read()

        blocks = content.strip().split("\n\n")
        for block in blocks:
            lines = block.strip().split("\n")
            if len(lines) < 3:
                continue

            timecode = lines[1]
            match = re.match(
                r"(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2}),(\d{3})",
                timecode
            )
            if not match:
                continue

            h1, m1, s1, ms1, h2, m2, s2, ms2 = map(int, match.groups())
            start_ms = (h1 * 3600 + m1 * 60 + s1) * 1000 + ms1
            end_ms = (h2 * 3600 + m2 * 60 + s2) * 1000 + ms2
            text = "\n".join(lines[2:])
            subtitles.append((start_ms, end_ms, text))
    except:
        pass
    return subtitles


# =================================================================
#                       REPRODUCTOR DE AUDIO
# =================================================================
class musicPlayer:
    def __init__(self, master):
        # Ventana y configuración base
        self.master = master
        self.master.title("Reproductor de Audio")
        self.master.configure(bg=DARK_BG)

        # Tamaño base para escalar widgets (por proporción)
        self.base_width = 700
        self.base_height = 230
        self.base_font_size = 10
        self.centerWindow(self.base_width, self.base_height)
        self.master.resizable(True, True)
        self.master.protocol("WM_DELETE_WINDOW", self.onClose)

        # Fuente propia para UI del reproductor de audio (para escalar con la ventana)
        self.ui_font = tkfont.Font(family=FONT_FAMILY, size=self.base_font_size)

        # Instancia de VLC (solo MediaPlayer, sencillo)
        self.player = vlc.MediaPlayer()

        # --- LAYOUT PRINCIPAL (USANDO PACK) ---
        # Frame de contenido central
        mainFrame = tk.Frame(master, bg=DARK_BG)
        mainFrame.pack(fill="both", expand=True, padx=10, pady=(10, 0))

        # Frame de controles abajo
        controlsFrame = tk.Frame(master, bg=DARK_BG)
        controlsFrame.pack(side="bottom", fill="x", pady=12)

        # Botón Reproducir
        self.playButton = tk.Button(
            controlsFrame, text="▶ Reproducir",
            command=self.playAudio, state="disabled",
            bg=BUTTON_BG, fg=TEXT_COLOR, relief="flat",
            font=self.ui_font
        )
        self.playButton.pack(side="left", padx=8, fill="x", expand=True)

        # Botón Pausar/Reanudar
        self.pauseButton = tk.Button(
            controlsFrame, text="⏸ Pausar",
            command=self.pauseAudio, state="disabled",
            bg=BUTTON_BG, fg=TEXT_COLOR, relief="flat",
            font=self.ui_font
        )
        self.pauseButton.pack(side="left", padx=8, fill="x", expand=True)

        # Botón Detener
        self.stopButton = tk.Button(
            controlsFrame, text="⏹ Detener",
            command=self.stopAudio, state="disabled",
            bg=BUTTON_BG, fg=TEXT_COLOR, relief="flat",
            font=self.ui_font
        )
        self.stopButton.pack(side="left", padx=8, fill="x", expand=True)

        # Botón Cargar
        self.loadButton = tk.Button(
            controlsFrame, text="📂 Cargar Audio",
            command=self.loadFile, bg=ACCENT_COLOR, fg=DARKER_BG,
            relief="flat", font=self.ui_font
        )
        self.loadButton.pack(side="right", padx=8, fill="x", expand=True)

        # Slider de progreso (tiempo) que se adapta al ancho
        self.progress = ttk.Scale(
            mainFrame,
            from_=0,
            to=0,
            orient="horizontal",
            style="Modern.Horizontal.TScale"
        )
        self.progress.pack(pady=(10, 0), fill="x")
        self.progress.bind("<ButtonRelease-1>", self.onSliderRelease)

        # Frame para tiempo actual / total
        tf = tk.Frame(mainFrame, bg=DARK_BG)
        tf.pack(fill="x", padx=30, pady=5)

        self.currentTime = tk.Label(tf, text="0:00", bg=DARK_BG,
                                    fg=TEXT_COLOR, font=self.ui_font)
        self.currentTime.pack(side="left")

        self.totalTime = tk.Label(tf, text="0:00", bg=DARK_BG,
                                  fg=TEXT_COLOR, font=self.ui_font)
        self.totalTime.pack(side="right")

        # Frame y slider de volumen
        volFrame = tk.Frame(mainFrame, bg=DARK_BG)
        volFrame.pack(pady=(5, 0), fill="x")

        volLabel = tk.Label(volFrame, text="Volumen",
                            bg=DARK_BG, fg=TEXT_COLOR, font=self.ui_font)
        volLabel.pack(side="left", padx=(0, 10))

        self.volumeScale = ttk.Scale(
            volFrame,
            from_=0,
            to=100,
            orient="horizontal",
            style="Modern.Horizontal.TScale",
            command=self.onVolumeChange
        )
        self.volumeScale.pack(side="left", fill="x", expand=True)
        self.volumeScale.set(100)

        # Establecer volumen inicial al 100%
        self.player.audio_set_volume(100)

        # Etiqueta "Reproduciendo ahora"
        self.nowPlaying = tk.Label(mainFrame, text="",
                                   fg=ACCENT_COLOR, bg=DARK_BG,
                                   font=self.ui_font)
        self.nowPlaying.pack(pady=8, fill="x")

        # Variables internas de estado del audio
        self.audioFile = None
        self.isPlaying = False
        self.isPaused = False
        self.duration = 0
        self.updatingProgress = False
        self.updateThread = None
        self.sliderUpdating = False

        # Vincular redimensionado de ventana para escalar fuente
        self.master.bind("<Configure>", self.on_resize)

    # --- EVENTO DE REDIMENSIÓN DE VENTANA (AUDIO) ---
    def on_resize(self, event):
        """
        Ajusta el tamaño de la fuente de los widgets según el tamaño actual
        de la ventana, usando como referencia las dimensiones base.
        """
        if event.widget is not self.master:
            return
        w = max(event.width, 1)
        h = max(event.height, 1)
        scale = min(w / self.base_width, h / self.base_height)
        new_size = max(8, int(self.base_font_size * scale))
        self.ui_font.configure(size=new_size)

    # --- CARGAR ARCHIVO DE AUDIO ---
    def loadFile(self):
        filetypes = [
            ("Audio", "*.mp3 *.wav *.flac *.ogg *.aac *.m4a"),
            ("Todos los archivos", "*.*")
        ]
        path = filedialog.askopenfilename(filetypes=filetypes)
        if not path:
            return
        self.audioFile = path

        # Reiniciar reproductor VLC con el nuevo archivo
        self.player.stop()
        self.player = vlc.MediaPlayer(path)
        try:
            self.player.audio_set_volume(int(self.volumeScale.get()))
        except:
            pass

        # Resetear estado de sliders y tiempos
        self.duration = 0
        self.progress.configure(from_=0, to=0)
        self.progress.set(0)
        self.currentTime.config(text="0:00")
        self.totalTime.config(text="0:00")
        self.nowPlaying.config(text="Cargado: " + path.split("/")[-1])

        # Habilitar botón de reproducción
        self.playButton.config(state="normal")
        self.pauseButton.config(state="disabled")
        self.stopButton.config(state="disabled")

    # --- REPRODUCIR AUDIO ---
    def playAudio(self):
        if not self.audioFile:
            return

        self.player.play()
        try:
            self.player.audio_set_volume(int(self.volumeScale.get()))
        except:
            pass

        self.isPlaying = True
        self.isPaused = False
        self.updatingProgress = True

        self.playButton.config(state="disabled")
        self.pauseButton.config(state="normal")
        self.stopButton.config(state="normal")

        # Hilo que mantiene el slider sincronizado con el tiempo real
        if not self.updateThread or not self.updateThread.is_alive():
            self.updateThread = threading.Thread(
                target=self.updateSliderThread,
                daemon=True
            )
            self.updateThread.start()

    # --- HILO: ACTUALIZAR SLIDER / TIEMPOS (AUDIO) ---
    def updateSliderThread(self):
        """
        Inicialmente intenta obtener la duración real.
        Después, mientras se reproduce, actualiza el slider y
        las etiquetas de tiempo cada 200 ms.
        """
        tries = 0
        # Intentar leer la longitud del archivo
        while self.updatingProgress and self.duration == 0 and tries < 20:
            length_ms = self.player.get_length()
            if length_ms and length_ms > 0:
                total_sec = length_ms // 1000
                self.duration = total_sec
                self.sliderUpdating = True
                self.progress.configure(to=total_sec)
                self.progress.set(0)
                self.sliderUpdating = False
                self.totalTime.config(text=self.formatTime(total_sec))
                break
            tries += 1
            time.sleep(0.2)

        # Bucle principal de actualización de tiempo
        while self.updatingProgress and self.isPlaying:
            if not self.isPaused:
                length_ms = self.player.get_length()
                if length_ms > 0:
                    total_sec = length_ms // 1000
                    cur_ms = self.player.get_time()
                    cur_sec = max(0, cur_ms // 1000)

                    self.sliderUpdating = True
                    self.progress.configure(to=total_sec)
                    self.progress.set(cur_sec)
                    self.sliderUpdating = False

                    self.currentTime.config(text=self.formatTime(cur_sec))
                    self.totalTime.config(text=self.formatTime(total_sec))
            time.sleep(0.2)

    # --- CUANDO SE SUELTA EL SLIDER (AUDIO) ---
    def onSliderRelease(self, event):
        if self.sliderUpdating or not self.audioFile:
            return
        value = self.progress.get()
        self.updatePos(value)

    # --- CAMBIO DE VOLUMEN ---
    def onVolumeChange(self, value):
        try:
            self.player.audio_set_volume(int(float(value)))
        except:
            pass

    # --- PAUSAR / REANUDAR ---
    def pauseAudio(self):
        if not self.isPlaying:
            return
        self.player.pause()
        self.isPaused = not self.isPaused
        self.pauseButton.config(
            text="▶ Reanudar" if self.isPaused else "⏸ Pausar"
        )

    # --- DETENER AUDIO ---
    def stopAudio(self):
        self.isPlaying = False
        self.updatingProgress = False
        try:
            self.player.stop()
        except:
            pass
        self.isPaused = False
        self.progress.set(0)
        self.currentTime.config(text="0:00")
        self.totalTime.config(
            text=self.formatTime(self.duration) if self.duration > 0 else "0:00"
        )
        self.nowPlaying.config(text="")
        self.playButton.config(state="normal")
        self.pauseButton.config(state="disabled", text="⏸ Pausar")
        self.stopButton.config(state="disabled")

    # --- SALTO DE POSICIÓN EN EL AUDIO DESDE EL SLIDER ---
    def updatePos(self, value):
        if self.sliderUpdating or not self.audioFile:
            return
        seconds = float(value)
        if self.isPlaying:
            try:
                self.player.set_time(int(seconds * 1000))
            except:
                pass
        self.currentTime.config(text=self.formatTime(seconds))

    # --- FORMATEO DE SEGUNDOS A M:SS ---
    def formatTime(self, seconds):
        seconds = int(seconds)
        m = seconds // 60
        s = seconds % 60
        return f"{m}:{s:02}"

    # --- CENTRAR VENTANA EN PANTALLA ---
    def centerWindow(self, w, h):
        sw = self.master.winfo_screenwidth()
        sh = self.master.winfo_screenheight()
        x = (sw // 2) - (w // 2)
        y = (sh // 2) - (h // 2)
        self.master.geometry(f"{w}x{h}+{x}+{y}")

    # --- CIERRE SEGURO DE VENTANA ---
    def onClose(self):
        try:
            self.stopAudio()
        except:
            pass
        try:
            self.master.destroy()
        except:
            pass


# =================================================================
#                       REPRODUCTOR DE VIDEO
# =================================================================
class videoPlayer:
    def __init__(self, master):
        # Ventana y configuración base
        self.master = master
        self.master.title("Reproductor de Video")
        self.master.configure(bg=DARK_BG)

        # Tamaño base para escalar
        self.base_width = 900
        self.base_height = 650
        self.base_font_size = 10
        self.centerWindow(self.base_width, self.base_height)
        self.master.resizable(True, True)
        self.master.protocol("WM_DELETE_WINDOW", self.onClose)

        # Fuente de la UI del reproductor de vídeo
        self.ui_font = tkfont.Font(family=FONT_FAMILY, size=self.base_font_size)

        # Instancia VLC
        self.player = vlc.MediaPlayer()

        # Frame principal de contenido
        mainFrame = tk.Frame(master, bg=DARK_BG)
        mainFrame.pack(fill="both", expand=True, padx=10, pady=(10, 0))

        # Frame de controles inferior
        controlsFrame = tk.Frame(master, bg=DARK_BG)
        controlsFrame.pack(side="bottom", fill="x", pady=12)

        # Botón Reproducir
        self.playButton = tk.Button(
            controlsFrame, text="▶ Reproducir",
            command=self.playVideo, state="disabled",
            bg=BUTTON_BG, fg=TEXT_COLOR, relief="flat",
            font=self.ui_font
        )
        self.playButton.pack(side="left", padx=8, fill="x", expand=True)

        # Botón Pausar
        self.pauseButton = tk.Button(
            controlsFrame, text="⏸ Pausar",
            command=self.pauseVideo, state="disabled",
            bg=BUTTON_BG, fg=TEXT_COLOR, relief="flat",
            font=self.ui_font
        )
        self.pauseButton.pack(side="left", padx=8, fill="x", expand=True)

        # Botón Detener
        self.stopButton = tk.Button(
            controlsFrame, text="⏹ Detener",
            command=self.stopVideo, state="disabled",
            bg=BUTTON_BG, fg=TEXT_COLOR, relief="flat",
            font=self.ui_font
        )
        self.stopButton.pack(side="left", padx=8, fill="x", expand=True)

        # Botón Cargar Video
        self.loadButton = tk.Button(
            controlsFrame, text="📂 Cargar Video",
            command=self.loadFile, bg=ACCENT_COLOR, fg=DARKER_BG,
            relief="flat", font=self.ui_font
        )
        self.loadButton.pack(side="right", padx=8, fill="x", expand=True)

        # Botón Cargar Subtítulos
        self.loadSubtitleButton = tk.Button(
            controlsFrame, text="💬 Subtítulos",
            command=self.loadSubtitle, bg=ACCENT_COLOR, state="disabled",
            fg=DARKER_BG, relief="flat", font=self.ui_font
        )
        self.loadSubtitleButton.pack(side="right", padx=8, fill="x", expand=True)

        # Área de vídeo (ocupa prácticamente todo el espacio disponible)
        self.videoFrame = tk.Frame(mainFrame, bg=DARKER_BG)
        self.videoFrame.pack(pady=12, padx=20, fill="both", expand=True)

        # Ventana overlay para subtítulos
        self.subtitle_overlay = tk.Toplevel(self.master)
        self.subtitle_overlay.overrideredirect(True)
        self.subtitle_overlay.attributes("-topmost", True)
        self.subtitle_overlay.configure(bg="magenta")
        try:
            self.subtitle_overlay.wm_attributes("-transparentcolor", "magenta")
        except:
            pass
        self.subtitle_label = tk.Label(
            self.subtitle_overlay,
            text="",
            bg="magenta",
            fg="yellow",
            font=(FONT_FAMILY, 14),
            wraplength=600,
            justify="center"
        )
        self.subtitle_label.pack(expand=True, fill="both")
        self.subtitle_overlay.withdraw()

        # Reposicionar overlay cuando cambie el tamaño del frame de vídeo
        self.videoFrame.bind("<Configure>", lambda e: self.posSub())

        # Slider de progreso (0-1000) que ocupa todo el ancho
        self.progress = ttk.Scale(
            mainFrame,
            from_=0,
            to=1000,
            orient="horizontal",
            style="Modern.Horizontal.TScale"
        )
        self.progress.pack(pady=10, fill="x")
        self.progress.bind("<ButtonRelease-1>", self.onSliderRelease)

        # Frame para tiempos
        tf = tk.Frame(mainFrame, bg=DARK_BG)
        tf.pack(fill="x", padx=30, pady=5)

        self.currentTime = tk.Label(tf, text="0:00",
                                    bg=DARK_BG, fg=TEXT_COLOR,
                                    font=self.ui_font)
        self.currentTime.pack(side="left")

        self.totalTime = tk.Label(tf, text="0:00",
                                  bg=DARK_BG, fg=TEXT_COLOR,
                                  font=self.ui_font)
        self.totalTime.pack(side="right")

        # Frame volumen
        volFrame = tk.Frame(mainFrame, bg=DARK_BG)
        volFrame.pack(pady=(5, 0), fill="x")

        volLabel = tk.Label(volFrame, text="Volumen",
                            bg=DARK_BG, fg=TEXT_COLOR, font=self.ui_font)
        volLabel.pack(side="left", padx=(0, 10))

        self.volumeScale = ttk.Scale(
            volFrame,
            from_=0,
            to=100,
            orient="horizontal",
            style="Modern.Horizontal.TScale",
            command=self.onVolumeChange
        )
        self.volumeScale.pack(side="left", fill="x", expand=True)
        self.volumeScale.set(100)
        self.player.audio_set_volume(100)

        # Etiqueta "Reproduciendo ahora"
        self.nowPlaying = tk.Label(mainFrame, text="",
                                   fg=ACCENT_COLOR, bg=DARK_BG,
                                   font=self.ui_font)
        self.nowPlaying.pack(pady=8, fill="x")

        # Estado interno de vídeo
        self.videoFile = None
        self.subtitles = []
        self.isPlaying = False
        self.isPaused = False
        self.duration = 0
        self.sliderUpdating = False
        self.updatingProgress = False
        self.updateThread = None

        # Vincular redimensionado para escalar fuentes
        self.master.bind("<Configure>", self.on_resize)

    # --- EVENTO REDIMENSIÓN (VIDEO) ---
    def on_resize(self, event):
        """
        Redimensiona la fuente de la UI del reproductor de vídeo en función
        del tamaño de la ventana, manteniendo proporción con el tamaño base.
        """
        if event.widget is not self.master:
            return
        w = max(event.width, 1)
        h = max(event.height, 1)
        scale = min(w / self.base_width, h / self.base_height)
        new_size = max(8, int(self.base_font_size * scale))
        self.ui_font.configure(size=new_size)

    # --- CARGAR SUBTÍTULOS EXTERNOS ---
    def loadSubtitle(self):
        if not self.videoFile:
            return
        path = filedialog.askopenfilename(
            filetypes=[
                ("Subtítulos", "*.srt *.ass *.ssa *.vtt *.sub *.txt"),
                ("Todos los archivos", "*.*")
            ]
        )
        if not path:
            return
        # De momento solo parseamos SRT; otros formatos no se procesan a nivel texto
        self.subtitles = parseSRT(path)
        self.subtitle_overlay.deiconify()
        self.posSub()

    # --- CARGAR ARCHIVO DE VÍDEO ---
    def loadFile(self):
        path = filedialog.askopenfilename(
            filetypes=[
                ("Videos", "*.mp4 *.avi *.mkv *.mov *.flv *.wmv *.webm"),
                ("Todos los archivos", "*.*")
            ]
        )
        if not path:
            return
        self.videoFile = path

        self.player.stop()
        self.player = vlc.MediaPlayer(path)
        # Asociar la salida de vídeo al frame de Tk
        try:
            self.player.set_hwnd(self.videoFrame.winfo_id())
        except:
            pass
        try:
            self.player.audio_set_volume(int(self.volumeScale.get()))
        except:
            pass

        self.duration = 0
        self.progress.set(0)
        self.currentTime.config(text="0:00")
        self.totalTime.config(text="0:00")
        self.nowPlaying.config(text="Cargado: " + path.split("/")[-1])

        self.playButton.config(state="normal")
        self.pauseButton.config(state="disabled")
        self.stopButton.config(state="disabled")
        self.loadSubtitleButton.config(state="normal")

        self.posSub()
        self.subtitle_overlay.deiconify()

    # --- REPRODUCIR VÍDEO ---
    def playVideo(self):
        if not self.videoFile:
            return

        self.player.play()
        try:
            self.player.audio_set_volume(int(self.volumeScale.get()))
        except:
            pass

        self.isPlaying = True
        self.isPaused = False
        self.updatingProgress = True

        self.playButton.config(state="disabled")
        self.pauseButton.config(state="normal")
        self.stopButton.config(state="normal")

        # Hilo que mantiene el slider y subtítulos sincronizados
        if not self.updateThread or not self.updateThread.is_alive():
            self.updateThread = threading.Thread(
                target=self.updateSliderThread,
                daemon=True
            )
            self.updateThread.start()

    # --- HILO: ACTUALIZAR SLIDER / TIEMPOS / SUBTÍTULOS ---
    def updateSliderThread(self):
        """
        Mientras se reproduce el vídeo, actualiza el slider de posición,
        las etiquetas de tiempo y el texto de subtítulos.
        """
        while self.updatingProgress and self.isPlaying:
            if not self.isPaused:
                length = self.player.get_length()
                if length > 0:
                    cur_ms = self.player.get_time()
                    pos = cur_ms / length
                    if pos < 0 or pos > 1:
                        pos = 0.0

                    cur_sec = cur_ms // 1000
                    total_sec = length // 1000

                    self.sliderUpdating = True
                    self.progress.set(pos * 1000)
                    self.sliderUpdating = False

                    self.currentTime.config(text=self._formatTime(cur_sec))
                    self.totalTime.config(text=self._formatTime(total_sec))

                    self.updateSub(cur_ms)
            time.sleep(0.2)

    # --- CUANDO SE SUELTA EL SLIDER (VIDEO) ---
    def onSliderRelease(self, event):
        if self.sliderUpdating or not self.videoFile:
            return
        value = self.progress.get()
        self.updatePos(value)

    # --- CAMBIO DE VOLUMEN (VIDEO) ---
    def onVolumeChange(self, value):
        try:
            self.player.audio_set_volume(int(float(value)))
        except:
            pass

    # --- PAUSAR / REANUDAR VÍDEO ---
    def pauseVideo(self):
        if not self.isPlaying:
            return
        self.player.pause()
        self.isPaused = not self.isPaused
        self.pauseButton.config(
            text="▶ Reanudar" if self.isPaused else "⏸ Pausar"
        )

    # --- DETENER VÍDEO ---
    def stopVideo(self):
        self.isPlaying = False
        self.updatingProgress = False
        try:
            self.player.stop()
        except:
            pass
        self.isPaused = False
        self.progress.set(0)
        self.currentTime.config(text="0:00")
        self.totalTime.config(
            text=self._formatTime(self.duration) if self.duration > 0 else "0:00"
        )
        self.subtitle_label.config(text="")
        self.subtitle_overlay.withdraw()
        self.playButton.config(state="normal")
        self.pauseButton.config(state="disabled", text="⏸ Pausar")
        self.stopButton.config(state="disabled")

    # --- SALTO DE POSICIÓN DESDE EL SLIDER ---
    def updatePos(self, value):
        if self.sliderUpdating or not self.videoFile:
            return
        pos = float(value) / 1000.0
        if self.isPlaying:
            try:
                self.player.set_position(pos)
            except:
                pass
        else:
            self.progress.set(float(value))
            length = self.player.get_length() // 1000
            current = int(pos * length) if length > 0 else 0
            self.currentTime.config(text=self._formatTime(current))

    # --- ACTUALIZAR TEXTO DE SUBTÍTULOS SEGÚN TIEMPO ---
    def updateSub(self, t_ms):
        text = ""
        for start, end, s in self.subtitles:
            if start <= t_ms <= end:
                text = s
                break
        self.subtitle_label.config(text=text)

    # --- POSICIONAR OVERLAY DE SUBTÍTULOS SOBRE EL VÍDEO ---
    def posSub(self):
        try:
            self.master.update_idletasks()
            x = self.videoFrame.winfo_rootx()
            y = self.videoFrame.winfo_rooty()
            w = self.videoFrame.winfo_width()
            h = self.videoFrame.winfo_height()
            self.subtitle_overlay.geometry(
                f"{w}x{int(h*0.18)}+{x}+{y+h-int(h*0.18)-8}"
            )
            self.subtitle_label.config(wraplength=int(w * 0.9))
        except:
            pass

    # --- FORMATEO DE SEGUNDOS A M:SS ---
    def _formatTime(self, seconds):
        seconds = int(seconds)
        m = seconds // 60
        s = seconds % 60
        return f"{m}:{s:02}"

    # --- CENTRAR VENTANA EN PANTALLA ---
    def centerWindow(self, w, h):
        sw = self.master.winfo_screenwidth()
        sh = self.master.winfo_screenheight()
        x = (sw // 2) - (w // 2)
        y = (sh // 2) - (h // 2)
        self.master.geometry(f"{w}x{h}+{x}+{y}")

    # --- CIERRE SEGURO DE VENTANA ---
    def onClose(self):
        try:
            self.stopVideo()
        except:
            pass
        try:
            self.master.destroy()
        except:
            pass


# =================================================================
#                         MENÚ PRINCIPAL
# =================================================================
class mainApp:
    def __init__(self, master):
        # Ventana principal
        self.master = master
        self.master.title("Reproductor Multimedia")
        self.master.configure(bg=DARK_BG)

        # Tamaños base para escalado
        self.base_width = 400
        self.base_height = 400
        self.base_font_size = 10
        self.base_title_size = 18
        self.centerWindow(self.base_width, self.base_height)
        self.master.resizable(True, True)

        # Fuentes de la UI del menú
        self.ui_font = tkfont.Font(family=FONT_FAMILY, size=self.base_font_size)
        self.title_font = tkfont.Font(
            family=FONT_FAMILY,
            size=self.base_title_size,
            weight="bold"
        )

        # Contenedor central que se redimensiona
        container = tk.Frame(master, bg=DARK_BG)
        container.pack(fill="both", expand=True)

        container.grid_columnconfigure(0, weight=1)
        container.grid_columnconfigure(1, weight=0)
        container.grid_columnconfigure(2, weight=1)
        container.grid_rowconfigure(0, weight=1)
        container.grid_rowconfigure(4, weight=1)

        self.themeButton = tk.Button(
            container,
            text="🌙",
            width=5,
            command=self.toggleTheme,
            bg=THEMES[CURRENT_THEME]["button_bg"],
            fg=THEMES[CURRENT_THEME]["button_fg"],
            relief="flat",
            font=self.ui_font
        )
        self.themeButton.grid(row=0, column=1, pady=10, padx=10, sticky="ne")

        # Aplicar tema inicial
        applyTheme(self.master, THEMES[CURRENT_THEME])

        # Título principal
        t = tk.Label(container, text="Reproductor Multimedia",
                     font=self.title_font, fg=ACCENT_COLOR, bg=DARK_BG)
        t.grid(row=1, column=1, pady=20)

        # Botón de reproductor de audio
        self.audioButton = tk.Button(
            container, text="♫ Reproductor de Audio",
            command=self.openMusic,
            bg=BUTTON_BG, fg=TEXT_COLOR, relief="flat",
            font=self.ui_font
        )
        self.audioButton.grid(row=2, column=1, pady=10, padx=30, sticky="ew")

        # Botón de reproductor de vídeo
        self.videoButton = tk.Button(
            container, text="🎬 Reproductor de Video",
            command=self.openVideo,
            bg=BUTTON_BG, fg=TEXT_COLOR, relief="flat",
            font=self.ui_font
        )
        self.videoButton.grid(row=3, column=1, pady=10, padx=30, sticky="ew")

        # Vincular redimensionado para escalar fuentes
        self.master.bind("<Configure>", self.on_resize)

    # --- EVENTO REDIMENSIÓN (MENÚ PRINCIPAL) ---
    def on_resize(self, event):
        if event.widget is not self.master:
            return
        w = max(event.width, 1)
        h = max(event.height, 1)
        scale = min(w / self.base_width, h / self.base_height)
        new_base = max(8, int(self.base_font_size * scale))
        new_title = max(12, int(self.base_title_size * scale))
        self.ui_font.configure(size=new_base)
        self.title_font.configure(size=new_title)

    # --- ABRIR REPRODUCTOR DE AUDIO ---
    def openMusic(self):
        win = tk.Toplevel(self.master)
        win.resizable(True, True)
        musicPlayer(win)

    # --- ABRIR REPRODUCTOR DE VIDEO ---
    def openVideo(self):
        win = tk.Toplevel(self.master)
        win.resizable(True, True)
        videoPlayer(win)

    # --- CAMBIAR TEMA (CLARO/OSCURO) ---
    def toggleTheme(self):
        global CURRENT_THEME
        CURRENT_THEME = "light" if CURRENT_THEME == "dark" else "dark"
        self.themeButton.config(text="🌙" if CURRENT_THEME == "dark" else "☀️")
        applyTheme(self.master, THEMES[CURRENT_THEME])

    # --- CENTRAR VENTANA EN PANTALLA ---
    def centerWindow(self, w, h):
        sw = self.master.winfo_screenwidth()
        sh = self.master.winfo_screenheight()
        x = (sw // 2) - (w // 2)
        y = (sh // 2) - (h // 2)
        self.master.geometry(f"{w}x{h}+{x}+{y}")

if __name__ == "__main__":
    root = tk.Tk()
    init_styles(root)
    mainApp(root)
    root.mainloop()
