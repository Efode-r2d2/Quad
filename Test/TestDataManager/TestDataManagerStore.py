from Utilities import DirManager
from Utilities import AudioManager
from Core import STFT
from Core import PeakExtractor
from Core import FingerprintGenerator
from DataManager import DataManager

# Source directory for reference audio files
src_dir = "../../../Test_Data/Reference_Audios/"
# retrieving all reference audios under specified source directory
mp3_files = DirManager.find_mp3_files(src_dir=src_dir)
# loading time series audio data of one of reference audio
audio_data = AudioManager.load_audio(audio_path=mp3_files[1], sampling_rate=7000)
# an object for Short Time Fourier Transform
stft = STFT(n_fft=1024, hop_length=32, sr=7000)
# computing the spectrogram of time series audio data
spectrogram = stft.compute_stft_magnitude_in_db(audio_data=audio_data)
# an object to extract spectral peaks from STFT based spectrogram
peak_extractor = PeakExtractor(maximum_filter_width=150, maximum_filter_height=75)
# extracting spectral peaks from STFT based spectrogram
spectral_peaks = peak_extractor.extract_spectral_peaks_2(spectrogram=spectrogram)
# an object to generate fingerprints using the associtation of four spectral peaks
fingerprint_generator = FingerprintGenerator(target_zone_width=1, target_zone_center=2, tolerance=0.31)
# generate fingerprints using the association of four spectral peaks
audio_fingerprints = fingerprint_generator.__generate_fingerprints__(spectral_peaks=spectral_peaks[0])
# Data manager object
data_manager = DataManager("../../../Hashes/Quad/Quad.db")
# storing fingerprints
data_manager.__store__(fingerprints=audio_fingerprints, title="Audio1")
