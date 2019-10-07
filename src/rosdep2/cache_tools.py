# Copyright (c) 2012, Willow Garage, Inc.
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

import hashlib
import os
import tempfile

from .core import CachePermissionError

try:
    import cPickle as pickle
except ImportError:
    import pickle

PICKLE_CACHE_EXT = '.pickle'


def compute_filename_hash(key_filenames):
    sha_hash = hashlib.sha1()
    if isinstance(key_filenames, list):
        for key in key_filenames:
            sha_hash.update(key.encode())
    else:
        sha_hash.update(key_filenames.encode())
    return sha_hash.hexdigest()


def write_cache_file(source_cache_d, key_filenames, rosdep_data):
    """
    :param source_cache_d: directory to write cache file to
    :param key_filenames: filename (or list of filenames) to be used in hashing
    :param rosdep_data: dictionary of data to serialize as YAML
    :returns: name of file where cache is stored
    :raises: :exc:`OSError` if cannot write to cache file/directory
    :raises: :exc:`IOError` if cannot write to cache file/directory
    """
    if not os.path.exists(source_cache_d):
        os.makedirs(source_cache_d)
    key_hash = compute_filename_hash(key_filenames)
    filepath = os.path.join(source_cache_d, key_hash)
    try:
        write_atomic(filepath + PICKLE_CACHE_EXT, pickle.dumps(rosdep_data, 2), True)
    except OSError as e:
        raise CachePermissionError('Failed to write cache file: ' + str(e))
    try:
        os.unlink(filepath)
    except OSError:
        pass
    return filepath


def write_atomic(filepath, data, binary=False):
    # write data to new file
    fd, filepath_tmp = tempfile.mkstemp(prefix=os.path.basename(filepath) + '.tmp.', dir=os.path.dirname(filepath))

    if (binary):
        fmode = 'wb'
    else:
        fmode = 'w'

    with os.fdopen(fd, fmode) as f:
        f.write(data)
        f.close()

    try:
        # switch file atomically (if supported)
        os.rename(filepath_tmp, filepath)
    except OSError:
        # fall back to non-atomic operation
        try:
            os.unlink(filepath)
        except OSError:
            pass
        try:
            os.rename(filepath_tmp, filepath)
        except OSError:
            os.unlink(filepath_tmp)
