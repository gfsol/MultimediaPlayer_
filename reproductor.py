import tkinter as tk
from tkinter import filedialog
import pyaudio
import wave
import threading
import utils

class Reproductor:
    import tkinter as tk
from tkinter import ttk

class Reproductor:
    def __init__(self, master):
        self.master = master
        self.master.title("🎵 Reproductor Multimedia")
        self.master.geometry("400x300")
        self.master.configure(bg="#1e1e1e")  # Fondo oscuro elegante

        # 🎧 Título principal
        self.title_label = tk.Label(
            master,
            text="Reproductor Multimedia",
            font=("Segoe UI", 16, "bold"),
            bg="#1e1e1e",
            fg="#00bcd4"
        )
        self.title_label.pack(pady=20)

        # 🎶 Frame para los botones
        button_frame = tk.Frame(master, bg="#1e1e1e")
        button_frame.pack(pady=20)

        # Botones principales con estilo coherente
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "TButton",
            font=("Segoe UI", 11),
            padding=6,
            background="#00bcd4",
            foreground="white",
            borderwidth=0
        )
        style.map(
            "TButton",
            background=[("active", "#0097a7")]
        )

        self.play_button = ttk.Button(button_frame, text="▶ Reproducir", command=self.play_audio)
        self.play_button.grid(row=0, column=0, padx=10)

        self.stop_button = ttk.Button(button_frame, text="⏹ Detener", command=self.stop_audio)
        self.stop_button.grid(row=0, column=1, padx=10)

        self.load_button = ttk.Button(button_frame, text="📂 Cargar Archivo", command=self.load_file)
        self.load_button.grid(row=0, column=2, padx=10)

        # 🎵 Estado actual
        self.status_label = tk.Label(
            master,
            text="No se ha cargado ningún archivo",
            font=("Segoe UI", 10),
            bg="#1e1e1e",
            fg="#cccccc"
        )
        self.status_label.pack(pady=10)

        # 🎚️ Barra de progreso (opcional)
        self.progress = ttk.Progressbar(master, orient="horizontal", length=300, mode="determinate")
        self.progress.pack(pady=10)

        # Variables internas
        self.audio_thread = None
        self.is_playing = False
        self.audio_file = None


    def load_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Archivos de audio", "*.mp3 *.wav")])
        if file_path:
            if file_path.endswith('.mp3'):
                wav_path = file_path.rsplit('.', 1)[0] + '.wav'
                utils.mp3_to_wav(file_path, wav_path)
                self.audio_file = wav_path
            else:
                self.audio_file = file_path

    def play_audio(self):
        if self.audio_file and not self.is_playing:
            self.is_playing = True
            self.audio_thread = threading.Thread(target=self._play)
            self.audio_thread.start()

    def _play(self):
        chunk = 1024
        wf = wave.open(self.audio_file, 'rb')
        p = pyaudio.PyAudio()
        
        stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                        channels=wf.getnchannels(),
                        rate=wf.getframerate(),
                        output=True)
        
        data = wf.readframes(chunk)
        
        while data and self.is_playing:
            stream.write(data)
            data = wf.readframes(chunk)
        
        stream.stop_stream()
        stream.close()
        p.terminate()
        wf.close()
        self.is_playing = False

    def stop_audio(self):
        if self.is_playing:
            self.is_playing = False
            if self.audio_thread:
                self.audio_thread.join()
                
if __name__ == "__main__":
    root = tk.Tk()
    app = Reproductor(root)
    root.mainloop()