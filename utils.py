from pydub import AudioSegment

def mp3_to_wav(mp3_path, wav_path):
    """
    Convierte un archivo MP3 a WAV.
    
    :param mp3_path: Ruta del archivo MP3 de entrada.
    :param wav_path: Ruta del archivo WAV de salida.
    """
    audio = AudioSegment.from_mp3(mp3_path)
    audio.export(wav_path, format="wav")