from itertools import combinations
from bisect import bisect_left
from heapq import nlargest


class FingerprintGenerator(object):
    """
    This is a class used for extracting audio fingerprints given spectral peaks extracted from the audio. The
    fingerprints are extracted using the association of four spectral peaks called quads.

    Attributes:
        frames_per_second (int): Number of frames per second.
        target_zone_width (int): Width of the target zone in seconds.
        target_zone_center (int): Center of the target zone in seconds.
        tolerance (float): Maximum allowed tolerance to modifications.
        min_frame_number (int): Minimum frame number of assigned target zone.
        max_frame_number (int): Maximum frame number of the assigned target zone.
        number_of_quads_per_second (int): Number of quads per second.

    """

    def __init__(self, frames_per_second=219, target_zone_width=1, target_zone_center=4, number_of_quads_per_second=9,
                 tolerance=0.31):
        """
        A constructor method for a class FingerprintGenerator.

        Parameters:
            frames_per_second (int): Number of frames per second.
            target_zone_width (int): Width of the target zone in seconds.
            target_zone_center (int): Center of the target zone in seconds.
            tolerance (float): Maximum allowed tolerance to modifications.

        """
        self.frames_per_second = frames_per_second
        self.target_zone_width = target_zone_width
        self.target_zone_center = target_zone_center
        self.tolerance = tolerance
        self.min_frame_number = ((self.target_zone_center - self.target_zone_width / 2) * self.frames_per_second) / (
                1 + self.tolerance)
        self.max_frame_number = ((self.target_zone_center + self.target_zone_width / 2) * self.frames_per_second) / (
                1 - self.tolerance)
        self.number_of_quads_per_second = number_of_quads_per_second

    def generate_fingerprints(self, spectral_peaks, spectrogram):
        """
        A method to generate audio fingerprints using the association of four spectral peaks.

        Parameters:
            spectral_peaks (List): List of spectral peaks extracted from STFT based spectrogram of an audio.
            spectrogram (numpy.ndarray): Time-Frequency representation of an audio.

        Returns:
            List: List of audio fingerprints.

        """
        # extracting valid quads.
        valid_quads = self.__validate_quads(spectral_peaks=spectral_peaks)
        # strong quads per second audio.
        strong_quads = self.__strongest_quads(spectrogram=spectrogram, quads=valid_quads)
        # audio fingerprints extracted using the association of four spectral peaks.
        audio_fingerprints = self.__hash_quads(strong_quads=strong_quads)
        return audio_fingerprints

    def __validate_quads(self, spectral_peaks):
        """
        A method to extract valid quads per root peak.

        Parameters:
            spectral_peaks (List): List of spectral peaks.

        Returns:
            List : List of all valid quads.

        """
        valid_quads = list()
        for i in spectral_peaks:
            # a target zone for a given spectral peak
            target_zone = [j for j in spectral_peaks if
                           i[0] + self.min_frame_number <= j[0] <= i[
                               0] + self.max_frame_number]
            # all quads formed from a given target zone
            all_quads = list(combinations(target_zone, 3))
            for j in all_quads:
                a = i
                c = j[0]
                d = j[1]
                b = j[2]
                """
                Checking for a conditions:
                    Ax<Cx<=DX<=Bx,
                    Ay<By, Ay<Cy and
                    Dy<=By
                """
                if a[1] < c[1] < b[1] and a[1] < d[1] <= b[1]:
                    valid_quads.append((a,) + j)
        return valid_quads

    def __strongest_quads(self, spectrogram, quads):
        """
        A method to return n number of strong quads per second. Where n is passed as number of quads per second.

        Parameters:
            spectrogram (numpy.ndarray): Time-Frequency representation of an audio.
            quads (List) : All valid quads from spectral peaks of an audio.

        Returns:
            List: list of strongest quads.

        """
        strong_quads = []
        partitions = self.__find_partitions(quads)
        key = lambda p: (spectrogram[p[1][1]][p[1][0]] + spectrogram[p[2][1]][p[2][0]])
        for i in range(1, len(partitions)):
            start = partitions[i - 1]
            end = partitions[i]
            strong_quads += nlargest(self.number_of_quads_per_second, quads[start:end], key)
        return strong_quads

    def __find_partitions(self, quads):
        """
        A method to partition quads per second.

        Parameters:
            quads (List): List of all valid quads.

        Returns:
            List : list of valid quads per second.

        """
        b_l = bisect_left
        last_frame_number = quads[-1][0][0]
        num_partitions = last_frame_number // self.frames_per_second
        # creates a tuple of same form as the Quad namedtuple for bisecting
        quad = lambda x: ((x,), (), (), ())
        partitions = [b_l(quads, quad(i * self.frames_per_second)) for i in range(num_partitions)]
        partitions.append(len(quads))
        return partitions

    def __hash_quads(self, strong_quads):
        """
        A method to hash strong quads into distortion invariant audio fingerprints.

        Parameters:
            strong_quads (List): List of strong quads.

        Returns:
            List : List of audio fingerprints, each list item contains both the hash and raw data associated with the hash.
        """
        audio_fingerprints = list()
        for i in strong_quads:
            a = i[0]  # root peak (A), where a[0] tempo info and a[1] pitch info.
            c = i[1]  # C, c[0] tempo info and c[1] pitch info.
            d = i[2]  # D, d[0] tempo info and c[1] pitch info.
            b = i[3]  # B, b[0] tempo info and b[1] pitch info.
            # x_delta : tempo difference between the root peak (A) and B.
            x_delta = b[0] - a[0]
            # y_delta : pitch difference between the root peak (A) and B.
            y_delta = b[1] - a[1]
            # calculate the new value of cx_new
            cx_new = round(((c[0] - a[0]) / x_delta), 3)
            # calculate the new value of cy_new
            cy_new = round(((c[1] - a[1]) / y_delta), 3)
            # calculate the new value of dx_new
            dx_new = round(((d[0] - a[0]) / x_delta), 3)
            # calculate the new value of dy_new
            dy_new = round(((d[1] - a[1]) / y_delta), 3)
            # filtering fingerprints based on the
            if cx_new > (self.min_frame_number / self.max_frame_number) - 0.02:
                audio_fingerprints.append([[cx_new, cy_new, dx_new, dy_new], [a[0], a[1], b[0], b[1]]])
        return audio_fingerprints
