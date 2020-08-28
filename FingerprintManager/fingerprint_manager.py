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
from ConfigManager import config_manager
from DataManager import raw_data_manager
from DataManager import r_tree_manager


class FingerprintManager(object):
    def __init__(self, r_tree, shelf, config):
        self.r_tree = r_tree
        self.shelf = shelf
        self.config = config
        # r tree index
        self.r_tree_index = r_tree_manager.get_rtree_index(rtree_path=self.r_tree)
        # shelf index
        self.shelf_index = raw_data_manager.get_shelf_file_index(shelf_path=self.shelf)

    def __store_fingerprints__(self, audio_fingerprints, audio_id):
        """
        :param audio_fingerprints:
        :param audio_id:
        :return:
        """
        # node_id is used to identify each entry of the r_tree
        node_id = int(config_manager.read_config(config_file_path=self.config,
                                                 section="Default",
                                                 sub_section="Node_ID"))

        for i in audio_fingerprints:
            row = [audio_id] + i[1]
            r_tree_manager.insert_node(rtree_index=self.r_tree_index, node_id=node_id, hashes=i[0])
            raw_data_manager.insert_data(shelf=self.shelf_index, key=node_id, value=row)
            node_id += 1
        # updating the last node_id
        config_manager.write_config(config_file_path=self.config,
                                    section="Default",
                                    sub_section="Node_ID",
                                    value=str(node_id))
