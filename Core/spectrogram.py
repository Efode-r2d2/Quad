import librosa
import numpy as np


class Spectrogram(object):
    """
        Short time fourier transform bases transform function.
        Used to transform a time series audio data into its
        respective time-frequency representation (Spectrogram).
    """

    def __init__(self, n_fft=1024, hop_length=32, sr=7000):
        """

        :param n_fft:
        :param hop_length:
        """
        self.n_fft = n_fft
        self.hop_length = hop_length
        self.sr = sr

    def compute_stft(self, audio_data):
        """

        :param audio_data:
        :return:
        """
        stft = librosa.stft(y=audio_data, n_fft=self.n_fft, hop_length=self.hop_length)
        return stft

    def compute_stft_magnitude(self, audio_data):
        """

        :param audio_data:
        :return:
        """
        stft = self.compute_stft(audio_data)
        stft_magnitude = np.abs(stft)
        return stft_magnitude

    def compute_stft_magnitude_in_db(self, audio_data):
        """

        :param audio_data:
        :return:
        """
        spectrogram_magnitude = self.compute_stft_magnitude(audio_data)
        spectrogram_magnitude_in_db = librosa.amplitude_to_db(spectrogram_magnitude, ref=np.max)
        return spectrogram_magnitude_in_db
