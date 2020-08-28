from Utilities import dir_manager
from Utilities import audio_manager
from Core import Spectrogram

# source directory for reference audio files
src_dir = "../../../Test_Data/Reference_Audios/"
# retrieving all mp3 files under specified source directory
mp3_files = dir_manager.find_mp3_files(src_dir=src_dir)
# loading 10 second time series audio data from one of reference audios
audio_data = audio_manager.load_audio(audio_path=mp3_files[1], sampling_rate=7000, offset=10.0, duration=10.0)
# defining STFT object
spectrogram = Spectrogram(n_fft=1024, hop_length=32, sr=7000)
# computing spectrogram of an audio
spectrogram_magnitude_in_db = spectrogram.spectrogram_magnitude_in_db(audio_data=audio_data)
# spectrogram
print(spectrogram_magnitude_in_db)
