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

import os
import sys
import tempfile
import yaml
import urllib2

import rospkg.distro
import rosdep2.sources_list

def get_test_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), 'sources.list.d'))

def test_url_constants():
    from rosdep2.rep3 import REP3_TARGETS_URL
    for url_name, url in [('REP3_TARGETS_URL', REP3_TARGETS_URL),
                          ]:
        try:
            f = urllib2.urlopen(url)
            f.read()
            f.close()
        except:
            assert False, "URL [%s][%s] failed to download"%(url_name, url)

def test_download_targets_data():
    from rosdep2.rep3 import download_targets_data, REP3_TARGETS_URL
    from rosdep2 import DownloadFailure
    data = download_targets_data(REP3_TARGETS_URL)
    assert type(data) is dict
    assert 'electric' in data
    assert 'fuerte' in data
    assert 'lucid' in data['fuerte']
    assert 'oneiric' in data['fuerte']

    try:
        download_targets_data(targets_url='http://bad.ros.org/foo.yaml')
        assert False, "should have raised"
    except DownloadFailure:
        pass
