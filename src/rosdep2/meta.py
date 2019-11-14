# Copyright (c) 2019, Open Source Robotics Foundation, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of the Willow Garage, Inc. nor the names of its
#       contributors may be used to endorse or promote products derived from
#       this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import copy
import os
try:
    import cPickle as pickle
except ImportError:
    import pickle

try:
    FileNotFoundError
except NameError:
    # Python 2 compatibility
    # https://stackoverflow.com/questions/21367320/
    FileNotFoundError = IOError

import rospkg

from ._version import __version__
from .cache_tools import compute_filename_hash
from .cache_tools import write_cache_file
from .cache_tools import PICKLE_CACHE_EXT

"""
Rosdep needs to store data that isn't used to resolve rosdep keys, but needs to be cached during
`rosdep update`.
"""

META_CACHE_DIR = 'meta.cache'


def get_meta_cache_dir():
    """Return storage location for cached meta data."""
    ros_home = rospkg.get_ros_home()
    return os.path.join(ros_home, 'rosdep', META_CACHE_DIR)


class CacheWrapper(object):
    """Make it possible to introspect cache in case some future bug needs to be worked around."""

    def __init__(self, category, data):
        # The version of rosdep that wrote the category
        self.rosdep_version = __version__
        # The un-hashed name of the category
        self.category_name = category
        # The stuff being stored
        self.data = data

    @property
    def data(self):
        # If cached data type is mutable, don't allow modifications to what's been loaded
        return copy.deepcopy(self.__data)

    @data.setter
    def data(self, value):
        self.__data = copy.deepcopy(value)


class MetaDatabase:
    """
    Store and retrieve metadata from rosdep cache.

    This data is fetched during `rosdep update`, but is not a source for resolving rosdep keys.
    """

    def __init__(self, cache_dir=None):
        if cache_dir is None:
            cache_dir = get_meta_cache_dir()

        self._cache_dir = cache_dir
        self._loaded = {}

    def set(self, category, metadata):
        """Add or overwrite metadata in the cache."""
        wrapper = CacheWrapper(category, metadata)
        # print(category, metadata)
        write_cache_file(self._cache_dir, category, wrapper)
        self._loaded[category] = wrapper

    def get(self, category, default=None):
        """Return metadata in the cache, or None if there is no cache entry."""
        if category not in self._loaded:
            self._load_from_cache(category, self._cache_dir)

        if category in self._loaded:
            return self._loaded[category].data

        return default

    def _load_from_cache(self, category, cache_dir):
        filename = compute_filename_hash(category) + PICKLE_CACHE_EXT
        try:
            with open(os.path.join(self._cache_dir, filename), 'rb') as cache_file:
                self._loaded[category] = pickle.loads(cache_file.read())
        except FileNotFoundError:
            pass
