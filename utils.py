from pydub import AudioSegment

def mp3_to_wav(mp3Path, wavPath):

    audio = AudioSegment.from_mp3(mp3Path)
    audio.export(wavPath, format="wav")