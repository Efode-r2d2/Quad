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
from rtree import index
import rtree


def get_rtree_index(rtree_path):
    """

    :param rtree_path:
    :return:
    """
    p = rtree.index.Property()
    file_idx = index.Index(rtree_path, properties=p)
    return file_idx


def insert_node(rtree_index, node_id, hashes):
    """

    :param rtree_index:
    :param node_id:
    :param hashes:
    """
    rtree_index.insert(node_id, (hashes[0], hashes[1], hashes[2], hashes[3]))


def get_nearest_node(rtree_index, hashes):
    """

    :param rtree_index:
    :param hashes:
    :return:
    """
    return list(rtree_index.nearest((hashes[0], hashes[1], hashes[2], hashes[3]), 5))
