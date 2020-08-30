from Utilities import dir_manager
from Utilities import audio_manager
from Core import STFT
from Core import PeakExtractor
from Core import FingerprintGenerator
from DataManager import DataManager

# Source directory for reference audio files
src_dir = "../../../Test_Data/Reference_Audios/"
# retrieving all reference audios under specified source directory
reference_audios = dir_manager.find_mp3_files(src_dir=src_dir)
# an object for Short Time Fourier Transform
stft = STFT(n_fft=1024, hop_length=32, sr=7000)
# an object to extract spectral peaks from STFT based spectrogram
peak_extractor = PeakExtractor(maximum_filter_width=150, maximum_filter_height=75)
# an object to generate fingerprints using the associtation of four spectral peaks
fingerprint_generator = FingerprintGenerator(target_zone_width=1, target_zone_center=2, tolerance=0.31)
# Data manager object
data_manager = DataManager("../../../Hashes/Quad/Quad.db")
for i in reference_audios:
    audio_title = i.split("/")[5].split(".")[0]
    # loading time series audio data of one of reference audio
    audio_data = audio_manager.load_audio(audio_path=i, sr=7000)
    # computing the spectrogram of time series audio data
    spectrogram = stft.compute_spectrogram_magnitude_in_db(audio_data=audio_data)
    # extracting spectral peaks from STFT based spectrogram
    spectral_peaks = peak_extractor.spectral_peaks(spectrogram=spectrogram)
    # generate fingerprints using the association of four spectral peaks
    audio_fingerprints = fingerprint_generator.generate_fingerprints(spectral_peaks=spectral_peaks[0],
                                                                     spectrogram=spectrogram, number_of_quads_per_second=20)
    # storing fingerprints
    data_manager.store_fingerprints(audio_fingerprints=audio_fingerprints, spectral_peaks=spectral_peaks[0], audio_title=audio_title)
    print("Done Fingerprinting ", audio_title)
