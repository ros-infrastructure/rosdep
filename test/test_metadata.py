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

from __future__ import print_function

import os
import sys

try:
    from tempfile import TemporaryDirectory
except ImportError:
    import tempfile
    import shutil

    class TemporaryDirectory(object):
        """Python 2 compatible class."""

        def __init__(self):
            self.name = None

        def __enter__(self):
            self.name = tempfile.mkdtemp()
            return self.name

        def __exit__(self, t, v, tb):
            shutil.rmtree(self.name)

from rosdep2.meta import MetaDatabase


def test_metadatabase_set_get():
    with TemporaryDirectory() as tmpdir:
        db = MetaDatabase(cache_dir=tmpdir)
        db.set('fruit', 'tomato')
        assert 'tomato' == db.get('fruit')


def test_metadatabase_get_none():
    with TemporaryDirectory() as tmpdir:
        db = MetaDatabase(cache_dir=tmpdir)
        assert db.get('fruit') is None


def test_metadatabase_get_default():
    with TemporaryDirectory() as tmpdir:
        db = MetaDatabase(cache_dir=tmpdir)
        assert db.get('fruit', default='foo') == 'foo'
        db.set('fruit', 'tomato')
        assert db.get('fruit', default='foo') != 'foo'


def test_metadatabase_get_mutate_get():
    with TemporaryDirectory() as tmpdir:
        db = MetaDatabase(cache_dir=tmpdir)
        mutable = [1, 2, 3]
        db.set('category', mutable)
        mutable.append(4)
        assert [1, 2, 3] == db.get('category')


def test_metadatabase_set_set_get():
    with TemporaryDirectory() as tmpdir:
        db = MetaDatabase(cache_dir=tmpdir)
        db.set('fruit', 'tomato')
        db.set('fruit', 'orange')
        assert 'orange' == db.get('fruit')


def test_metadatabase_set_load_from_disk_get():
    with TemporaryDirectory() as tmpdir:
        db1 = MetaDatabase(cache_dir=tmpdir)
        db1.set('fruit', 'apple')

        db2 = MetaDatabase(cache_dir=tmpdir)
        assert 'apple' == db2.get('fruit')
