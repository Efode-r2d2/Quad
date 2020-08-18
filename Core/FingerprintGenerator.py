"""
    < Quad based audio fingerprinting system>
    Copyright (C) <2019>  <Efriem Desalew Gebie>

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
from itertools import combinations


def __validate_quads__(root_peak, all_quads, valid_quads):
    for i in all_quads:
        a = root_peak
        c = i[0]
        d = i[1]
        b = i[2]

        if a[0] < c[0] < d[0] < b[0] and a[1] < c[1] < d[1] < b[1]:
            valid_quads.append(i)


class FingerprintGenerator(object):
    def __init__(self, frames_per_second=219, target_zone_width=1, target_zone_center=4, tolerance=0.31):
        self.frames_per_second = frames_per_second
        self.target_zone_width = target_zone_width
        self.target_zone_center = target_zone_center
        self.tolerance = tolerance
        self.min_frame_number = ((self.target_zone_center - self.target_zone_width / 2) * self.frames_per_second) / (
                1 + self.tolerance)
        self.max_frame_number = ((self.target_zone_center + self.target_zone_width / 2) * self.frames_per_second) / (
                1 - self.tolerance)

    def __generate_fingerprints__(self, spectral_peaks):
        audio_fingerprints = list()
        for i in spectral_peaks:
            # list object to hold all valid quads within a given target zone
            valid_quads = list()
            # a target zone for a given spectral peak
            target_zone = [j for j in spectral_peaks if
                           i[0] + self.min_frame_number <= j[0] <= i[
                               0] + self.max_frame_number]
            # all quads formed from a given target zone
            all_quads = list(combinations(target_zone, 3))
            # validate quads formed form a given target zone and identify the valid ones
            if len(all_quads) > 0:
                __validate_quads__(root_peak=i, all_quads=all_quads, valid_quads=valid_quads)
            if len(valid_quads) > 0:
                self.__hash_quads__(root_peak=i, valid_quads=valid_quads,
                                    audio_fingerprints=audio_fingerprints)
        return audio_fingerprints

    def __hash_quads__(self, root_peak, valid_quads, audio_fingerprints):
        for i in valid_quads:
            a = root_peak
            c = i[0]
            d = i[1]
            b = i[2]
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
