from Utilities import dir_manager
from Utilities import audio_manager
from Core import STFT
from Core import PeakExtractor

# source directory for reference audio files
src_dir = "../../../Test_Data/Reference_Audios/"
# retrieving all mp3 files under specified source directory
mp3_files = dir_manager.find_mp3_files(src_dir=src_dir)
# loading 10 seconds time series audio data from one of the reference audio file
audio_data = audio_manager.load_audio(audio_path=mp3_files[1], sr=7000, offset=10.0, duration=10.0)
# computing STFT based spectrogram for a respective time series audio data
stft = STFT(n_fft=1024, hop_length=32, sr=7000)
spectrogram = stft.compute_spectrogram_magnitude_in_db(audio_data=audio_data)
# extracting spectral peaks from STFT based spectrogram
peak_extractor = PeakExtractor(maximum_filter_height=75, maximum_filter_width=150)
spectral_peaks = peak_extractor.spectral_peaks(spectrogram=spectrogram)
print(spectral_peaks[0])

