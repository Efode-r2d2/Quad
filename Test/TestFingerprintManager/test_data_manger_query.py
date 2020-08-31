from Utilities import dir_manager
from Utilities import audio_manager
from Core import STFT
from Core import PeakExtractor
from Core import FingerprintGenerator
from FingerprintManager import FingerprintManager
import time
import csv

# source directory for query audios
src_dir = "../../../Test_Data/Modified_Audios_2/White_Noise/0/"
# an object for computing stft based spectrogram
stft = STFT(n_fft=1024, hop_length=32, sr=700)
# an object to extract spectral peaks from stft based spectrogram
peak_extractor = PeakExtractor(maximum_filter_width=150, maximum_filter_height=75)
# an object to generate quad based audio fingerprints
fingerprint_generator = FingerprintGenerator(
    frames_per_second=219,
    target_zone_width=1,
    target_zone_center=2,
    number_of_quads_per_second=9,
    tolerance=0.31)
# FingerprintManager object
fingerprint_manager = FingerprintManager(db_path="../../../Databases/Quads_Test.db")
# results path
result_path = "../../../Results_2/Quad/Granularity/"
for t in range(5, 35, 5):
    query_audios = dir_manager.find_wav_files(src_dir=src_dir)
    dir_manager.create_dir(result_path)
    count = 901
    for i in query_audios:
        audio_id = i.split("/")[7].split(".")[0]
        # loading a time series audio data from one of the query audio
        start = time.time()
        audio_data = audio_manager.load_audio(audio_path=i,
                                              sr=7000,
                                              offset=10.0,
                                              duration=t)
        # computing stft based spectrogram of time series audio data
        spectrogram = stft.compute_spectrogram_magnitude_in_db(audio_data=audio_data)
        # extracting spectral peaks from STFT based spectrogram
        spectral_peaks = peak_extractor.spectral_peaks(spectrogram=spectrogram)
        # generate quad based fingerprints
        audio_fingerprints = fingerprint_generator.generate_fingerprints(spectral_peaks=spectral_peaks[0],
                                                                         spectrogram=spectrogram,
                                                                         number_of_quads_per_second=500)
        # query matches
        match = fingerprint_manager.query_audio(audio_fingerprints=audio_fingerprints, spectral_peaks=spectral_peaks[0],
                                                vThreshold=0.3)
        end = time.time()

        result = None
        if match[0] == "No Match":
            result = "False Negative"
        else:
            if audio_id == match[0]:
                result = "True Positive"
            else:
                result = "False Positive"
        row = [count, audio_id, match[0], result, end - start, match[1]]
        with open(result_path + str(t) + "_sec.csv", 'a') as csvFile:
            writer = csv.writer(csvFile)
            writer.writerow(row)
        csvFile.close()
        print("Seq", "Requested With; ", "Response; ", "Result Tag;", "Execution Time;",
              "Number of Matched Hashes;")
        print(count, audio_id, match[0], result, end - start, match[1])
        count += 1
