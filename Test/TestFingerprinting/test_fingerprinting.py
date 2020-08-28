from Utilities import dir_manager
from Utilities import audio_manager
from Core import Spectrogram
from Core import PeakExtractor
from Core import FingerprintGenerator
from FingerprintManager import FingerprintManager

# r tree path
r_tree = "../../../Hashes/Quad/Test_1"
# raw_data_path
shelf = "../../../Raw_Data/Quad/Test_1"
# config file path
config = "../../Config/Config_Quad.ini"
# source directory for reference audio files
src_dir = "../../../Test_Data/Reference_Audios"
# retrieving all reference audios under specified source directory
reference_audios = dir_manager.find_mp3_files(src_dir=src_dir)
# Declaring an object for Short Time Fourier Transform (STFT)
stft = Spectrogram(n_fft=1024, hop_length=32, sr=7000)
# Spectral peak extractor object
peak_extractor = PeakExtractor(maximum_filter_width=150, maximum_filter_height=75)
# Fingerprint generator object
fingerprint_generator = FingerprintGenerator(target_zone_width=1, target_zone_center=2, tolerance=0.0)
# Fingerprint Manager Object
fingerprint_manager = FingerprintManager(r_tree=r_tree, shelf=shelf, config=config)
# fingerprinting all reference audios
for i in reference_audios[0:10]:
    # audio_id
    audio_id = i.split("/")[5].split(".")[0]
    # reading time series audio data sampled at 7KHz
    audio_data = audio_manager.load_audio(audio_path=i, sampling_rate=7000)
    # computing stft based spectrogram
    spectrogram = stft.spectrogram_magnitude_in_db(audio_data=audio_data)
    # extracting spectral peaks from respective spectrogram
    spectral_peaks = peak_extractor.extract_spectral_peaks_2(spectrogram=spectrogram)
    # generating audio fingerprints
    audio_fingerprints = fingerprint_generator.__generate_fingerprints__(spectral_peaks=spectral_peaks[0])
    # storing generated fingerprints
    fingerprint_manager.__store_fingerprints__(audio_fingerprints=audio_fingerprints, audio_id=audio_id)
    print(audio_id, " Fingerprinted!")
