from Utilities import dir_manager
from Utilities import audio_manager
from Core import Spectrogram
from Core import PeakExtractor
from Core import FingerprintGenerator

# source directory for reference audio files
src_dir = "../../../Test_Data/Reference_Audios/"
# retrieving all mp3 audio files under specified source directory
mp3_files = dir_manager.find_mp3_files(src_dir=src_dir)
# loading 10 seconds time series audio data from one of reference audio file
audio_data = audio_manager.load_audio(audio_path=mp3_files[1], offset=10.0, duration=10.0, sr=7000)
# computing STFT based spectrogram from times series audio data
stft = Spectrogram(n_fft=1024, hop_length=32, sr=7000)
spectrogram = stft.spectrogram_magnitude_in_db(audio_data=audio_data)
# extracting spectral peaks from STFT based spectrogram
peak_extractor = PeakExtractor(maximum_filter_height=75, maximum_filter_width=150)
spectral_peaks = peak_extractor.extract_spectral_peaks_2(spectrogram=spectrogram)
# generating audio fingerprints
fingerprint_generator = FingerprintGenerator(target_zone_width=1, target_zone_center=2, tolerance=0.31)
audio_fingerprints = fingerprint_generator.__generate_fingerprints__(spectral_peaks=spectral_peaks[0])
print(audio_fingerprints)
