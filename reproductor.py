import tkinter as tk
from tkinter import filedialog
import pyaudio
import wave
import threading
import utils

class Reproductor:
    def __init__(self, root):
        self.root = root
        self.root.title("Reproductor de Audio")
        self.root.geometry("1280x720")

        # Botones
        self.btn_cargar = tk.Button(root, text="Cargar archivo", command=self.cargar_archivo)
        self.btn_cargar.pack(pady=10)

        self.btn_play = tk.Button(root, text="Reproducir", command=self.play_audio)
        self.btn_play.pack(pady=5)

        self.btn_stop = tk.Button(root, text="Detener", command=self.stop_audio)
        self.btn_stop.pack(pady=5)

        # Variables
        self.audio_file = None
        self.playing = False

    def cargar_archivo(self):
        ruta = filedialog.askopenfilename(filetypes=[("WAV files", "*.wav"), ("MP3 files", "*.mp3")])
        if ruta:
            self.audio_file = ruta
            print(f"Archivo cargado: {ruta}")

    def play_audio(self):
        if self.audio_file and not self.playing:
            self.playing = True
            threading.Thread(target=self._play_thread, daemon=True).start()

    def _play_thread(self):
        wf = wave.open(self.audio_file, 'rb')
        p = pyaudio.PyAudio()
        stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                        channels=wf.getnchannels(),
                        rate=wf.getframerate(),
                        output=True)

        data = wf.readframes(1024)
        while data and self.playing:
            stream.write(data)
            data = wf.readframes(1024)

        stream.stop_stream()
        stream.close()
        p.terminate()
        self.playing = False

    def stop_audio(self):
        self.playing = False

if __name__ == "__main__":
    root = tk.Tk()
    app = Reproductor(root)
    root.mainloop()
