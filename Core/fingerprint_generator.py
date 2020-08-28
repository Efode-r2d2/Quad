from itertools import combinations
from bisect import bisect_left
from heapq import nlargest


def validate_quads(root_peak, all_quads, valid_quads):
    for i in all_quads:
        a = root_peak
        c = i[0]
        d = i[1]
        b = i[2]

        if a[0] < c[0] < d[0] < b[0] and a[1] < c[1] < d[1] < b[1]:
            valid_quads.append((a,) + i)


def find_partitions(quads, number_of_frames_per_second=219):
    """
    Returns list of indices where partitions of 250 (1 second) are
    """
    b_l = bisect_left
    last_frame_number = quads[-1][0][0]
    num_partitions = last_frame_number // number_of_frames_per_second
    # creates a tuple of same form as the Quad namedtuple for bisecting
    quad = lambda x: ((x,), (), (), ())
    partitions = [b_l(quads, quad(i * number_of_frames_per_second)) for i in range(num_partitions)]
    partitions.append(len(quads))
    return partitions


def strongest_quads(spec, quads, n):
    """
    Returns list of n strongest quads in each 1 second partition
    Strongest is calculated by magnitudes of C and D in quad
    """
    strongest = []
    partitions = find_partitions(quads)
    key = lambda p: (spec[p[1][1]][p[1][0]] + spec[p[2][1]][p[2][0]])
    for i in range(1, len(partitions)):
        start = partitions[i - 1]
        end = partitions[i]
        strongest += nlargest(n, quads[start:end], key)
    return strongest


class FingerprintGenerator(object):

    """

    This is a class used for extracting audio fingerprints given spectral peaks extracted from the audio. The
    fingerprints are extracted using the association of four spectral peaks called quads.

    Attributes:
        frames_per_second (int): Number of frames per second.
        target_zone_width (int): Width of the target zone in seconds.


    """

    def __init__(self, frames_per_second=219, target_zone_width=1, target_zone_center=4, tolerance=0.31):
        self.frames_per_second = frames_per_second
        self.target_zone_width = target_zone_width
        self.target_zone_center = target_zone_center
        self.tolerance = tolerance
        self.min_frame_number = ((self.target_zone_center - self.target_zone_width / 2) * self.frames_per_second) / (
                1 + self.tolerance)
        self.max_frame_number = ((self.target_zone_center + self.target_zone_width / 2) * self.frames_per_second) / (
                1 - self.tolerance)

    def generate_fingerprints(self, spectral_peaks, spectrogram, n=9):
        audio_fingerprints = list()
        valid_quads = list()
        for i in spectral_peaks:
            # list object to hold all valid quads within a given target zone

            # a target zone for a given spectral peak
            target_zone = [j for j in spectral_peaks if
                           i[0] + self.min_frame_number <= j[0] <= i[
                               0] + self.max_frame_number]
            # all quads formed from a given target zone
            all_quads = list(combinations(target_zone, 3))

            # validate quads formed form a given target zone and identify the valid ones
            if len(all_quads) > 0:
                validate_quads(root_peak=i, all_quads=all_quads, valid_quads=valid_quads)

        strong_quads = strongest_quads(spec=spectrogram, quads=valid_quads, n=n)
        if len(strong_quads) > 0:
            self.__hash_quads(valid_quads=strong_quads,
                              audio_fingerprints=audio_fingerprints)
        return audio_fingerprints

    def __hash_quads(self, valid_quads, audio_fingerprints):
        for i in valid_quads:
            a = i[0]
            c = i[1]
            d = i[2]
            b = i[3]
            # calculate the new value of cx_new
            cx_new = round(((c[0] - a[0]) / (b[0] - a[0])), 3)
            # calculate the new value of cy_new
            cy_new = round(((c[1] - a[1]) / (b[1] - a[1])), 3)
            # calculate the new value of dx_new
            dx_new = round(((d[0] - a[0]) / (b[0] - a[0])), 3)
            # calculate the new value of dy_new
            dy_new = round(((d[1] - a[1]) / (b[1] - a[1])), 3)
            # filtering fingerprints based on the
            if cx_new > (self.min_frame_number / self.max_frame_number) - 0.02:
                audio_fingerprints.append([[cx_new, cy_new, dx_new, dy_new], [a[0], a[1], b[0], b[1]]])
