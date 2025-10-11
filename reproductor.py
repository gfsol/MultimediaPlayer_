import tkinter as tk
from tkinter import filedialog
import pyaudio
import wave
import threading
import utils
import time

class musicPlayer:
    def __init__(self, master):
        self.master = master
        self.master.title("Reproductor Multimedia")

        # --- FRAME (CONTENEDOR) PRINCIPAL DE CONTROLES ---
        controlsFrame = tk.Frame(master)
        controlsFrame.pack(pady=10)

        self.playButton = tk.Button(controlsFrame, text="▶ Reproducir", width=12, command=self.playAudio, state="disabled")
        self.playButton.grid(row=0, column=0, padx=5)

        self.pauseButton = tk.Button(controlsFrame, text="⏸ Pausar", width=12, command=self.pauseAudio, state="disabled")
        self.pauseButton.grid(row=0, column=1, padx=5)

        self.stopButton = tk.Button(controlsFrame, text="⏹ Detener", width=12, command=self.stopAudio, state="disabled")
        self.stopButton.grid(row=0, column=2, padx=5)

        self.loadButton = tk.Button(controlsFrame, text="📂 Cargar Archivo", width=15, command=self.loadFile)
        self.loadButton.grid(row=0, column=3, padx=5)

        # --- BARRA DE PROGRESO ---
        self.progress = tk.Scale(master, from_=0, to=0, orient="horizontal",
                                 length=400, showvalue=0, command=self.updatePosAudio)
        self.progress.pack(pady=(10, 0))

        # --- TIEMPOS ---
        self.timeFrame = tk.Frame(master)
        self.timeFrame.pack(fill="x", padx=20)

        self.currentTimeLabel = tk.Label(self.timeFrame, text="0:00")
        self.currentTimeLabel.pack(side="left")

        self.totalTimeLabel = tk.Label(self.timeFrame, text="0:00")
        self.totalTimeLabel.pack(side="right")

        # --- "REPRODUCIENDO AHORA" ---
        self.nowPlayingLabel = tk.Label(master, text="", font=("Arial", 10, "italic"), fg="green")
        self.nowPlayingLabel.pack(pady=5)

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
        filePath = filedialog.askopenfilename(filetypes=[("Archivos de audio", "*.mp3 *.wav")])
        if filePath:
            if filePath.endswith('.mp3'):
                wavPath = filePath.rsplit('.', 1)[0] + '.wav'
                utils.mp3_to_wav(filePath, wavPath)
                self.audioFile = wavPath
            else:
                self.audioFile = filePath

            waveFile = wave.open(self.audioFile, 'rb')
            self.totalFrames = waveFile.getnframes()
            self.frameRate = waveFile.getframerate()
            self.duration = self.totalFrames / self.frameRate
            waveFile.close()

            self.progress.config(from_=0, to=int(self.duration), resolution=0.1)
            self.progress.set(0)
            self.totalTimeLabel.config(text=self._formatTime(self.duration))
            self.currentTimeLabel.config(text="0:00")
            self.nowPlayingLabel.config(text="Archivo cargado: " + self.audioFile.split('/')[-1])

            self.playButton.config(state="normal")
            self.stopButton.config(state="disabled")
            self.pauseButton.config(state="disabled")
            self.playButton.config(state="normal")
    # Reproducir audio
    def playAudio(self):
        if self.audioFile and not self.isPlaying:
            self.isPlaying = True
            self.isPaused = False
            self.playButton.config(state="disabled")
            self.pauseButton.config(state="normal")
            self.stopButton.config(state="normal")

            fileName = self.audioFile.split("/")[-1].split(".")[0]
            self.nowPlayingLabel.config(text=f"Reproduciendo: {fileName}")

            self.audioThread = threading.Thread(target=self._playAudio, daemon=True)
            self.audioThread.start()
        elif self.isPaused:
            self.isPaused = False
    # Pausar audio
    def pauseAudio(self):
        if self.isPlaying:
            self.isPaused = not self.isPaused
            if self.isPaused:
                self.pauseButton.config(text="▶ Reanudar")
            else:
                self.pauseButton.config(text="⏸ Pausar")
    # Método para detener la reproducción
    def stopAudio(self):
        if self.isPlaying:
            self.isPlaying = False
            self.isPaused = False
            self.progress.set(0)
            self.currentTimeLabel.config(text="0:00")
            self.nowPlayingLabel.config(text="")
            self.playButton.config(state="normal")
            self.pauseButton.config(state="disabled", text="⏸ Pausar")
            self.stopButton.config(state="disabled")
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
    def updatePosAudio(self, value):
        if not self.audioFile:
            return
        seconds = float(value)
        if self.isPlaying:
            self.sliderChange = seconds
        else:
            self.progress.set(seconds)
            self.currentTimeLabel.config(text=self._formatTime(seconds))
    

if __name__ == "__main__":
    root = tk.Tk()
    app = musicPlayer(root)
    root.mainloop()