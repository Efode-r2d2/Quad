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
import threading
from DataManager import r_tree_manager
from DataManager import raw_data_manager
import numpy as np


class Match(threading.Thread):
    def run(self, matches_in_bins, rtree_index, raw_data_index, fingerprints, tolerance=0.31):
        for i in fingerprints:
            # getting raw data form query hashes
            p1x_q = i[1][0]
            p1y_q = i[1][1]
            p2x_q = i[1][2]
            p2y_q = i[1][3]

            min_t_delta = 1 / (1 + tolerance)
            max_t_delta = 1 / (1 - tolerance)
            min_f_delta = 1 / (1 + tolerance)
            max_f_delta = 1 / (1 - tolerance)

            candidate_matches = r_tree_manager.get_nearest_node(rtree_index, i[0])
            for m in candidate_matches:
                raw_data = raw_data_manager.get_data(shelf=raw_data_index, key=m)
                p1x_r = raw_data[1]
                p1y_r = raw_data[2]
                p2x_r = raw_data[3]
                p2y_r = raw_data[4]

                s_time = (p2x_q - p1x_q) / (p2x_r - p1x_r)
                s_freq = (p2y_q - p1y_q) / (p2y_r - p1y_r)
                if p1y_r == 0:
                    pitch_cho = 100
                else:
                    pitch_cho = p1y_q / p1y_r
                # first filter
                if min_t_delta < s_time < max_t_delta and min_f_delta < s_freq < max_f_delta:
                    # second filter
                    if 1 / (1 + tolerance) <= pitch_cho <= 1 / (1 - tolerance):
                        # third filter
                        if np.abs(p1y_q - p1y_r * s_freq) < 20.0:
                            matches_in_bins[raw_data[0]].append(p1x_r - p1x_q * s_time)
