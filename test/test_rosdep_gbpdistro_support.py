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
try:
    from urllib.request import urlopen
except ImportError:
    from urllib2 import urlopen


def get_test_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__),
                                        'sources.list.d'))


def test_url_constants():
    from rosdep2.gbpdistro_support import FUERTE_GBPDISTRO_URL
    for url_name, url in [
                          ('FUERTE_GBPDISTRO_URL', FUERTE_GBPDISTRO_URL)]:
        try:
            f = urlopen(url)
            f.read()
            f.close()
        except:
            assert False, "URL [%s][%s] failed to download" % (url_name, url)


def test_get_gbprepo_as_rosdep_data():
    from rosdep2.rosdistrohelper import get_index
    from rosdep2.gbpdistro_support import get_gbprepo_as_rosdep_data
    distro = list(get_index().distributions.keys())[0]
    data = get_gbprepo_as_rosdep_data(distro)
    for k in ['ros', 'catkin', 'genmsg']:
        assert k in data, data
    assert data['ros']['ubuntu']

    try:
        get_gbprepo_as_rosdep_data('fooNonExistantDistro')
        assert False, "should have raised"
    except RuntimeError:
        pass


def test_download_gbpdistro_as_rosdep_data():
    from rosdep2.gbpdistro_support import download_gbpdistro_as_rosdep_data
    from rosdep2.gbpdistro_support import FUERTE_GBPDISTRO_URL
    from rosdep2.rep3 import REP3_TARGETS_URL
    from rosdep2 import DownloadFailure
    data = download_gbpdistro_as_rosdep_data(FUERTE_GBPDISTRO_URL)
    # don't go beyond this, this test is just making sure the download
    # plumbing is correct, not the loader.
    for k in ['ros', 'catkin', 'genmsg']:
        assert k in data, data
    assert data['ros']['ubuntu']

    # try with bad url to trigger exception handling
    try:
        # override targets URL with bad URL
        download_gbpdistro_as_rosdep_data(FUERTE_GBPDISTRO_URL,
            targets_url='http://bad.ros.org/foo.yaml')
        assert False, "should have raised"
    except DownloadFailure:
        pass
    try:
        # use targets URL, which should have a bad format
        download_gbpdistro_as_rosdep_data(REP3_TARGETS_URL)
        assert False, "should have raised"
    except DownloadFailure:
        pass


def test_gbprepo_to_rosdep_data_on_bad_inputs():
    from rosdep2.gbpdistro_support import gbprepo_to_rosdep_data
    from rosdep2 import InvalidData
    simple_gbpdistro = {'release-name': 'foorte',
                        'repositories': {},
                        'type': 'gbp'}
    targets = {'foorte': ['lucid', 'oneiric']}
    # test bad data
    try:
        gbprepo_to_rosdep_data(simple_gbpdistro, [targets])
        assert False, "should have raised"
    except InvalidData:
        pass
    try:
        gbprepo_to_rosdep_data({
            'targets': 1,
            'repositories': [],
            'type': 'gbp'}, targets)
        assert False, "should have raised"
    except InvalidData:
        pass
    try:
        gbprepo_to_rosdep_data([], targets)
        assert False, "should have raised"
    except InvalidData:
        pass
    # release-name must be in targets
    try:
        gbprepo_to_rosdep_data({
            'release-name': 'barte',
            'repositories': [],
            'type': 'gbp'}, targets)
        assert False, "should have raised"
    except InvalidData:
        pass
    # gbp-distros must be list of dicts
    try:
        gbprepo_to_rosdep_data({
            'release-name': 'foorte',
            'repositories': [1],
            'type': 'gbp'}, targets)
        assert False, "should have raised"
    except InvalidData:
        pass
    # gbp-distro target must be 'all' or a list of strings
    try:
        bad_example = {'name': 'common',
                       'target': [1],
                       'url': 'git://github.com/wg-debs/common_msgs.git'}
        gbprepo_to_rosdep_data({
            'release-name': 'foorte',
            'repositories': [bad_example],
            'type': 'gbp'}, targets)
        assert False, "should have raised"
    except InvalidData:
        pass


def test_gbprepo_to_rosdep_data_on_ok_input():
    from rosdep2.gbpdistro_support import gbprepo_to_rosdep_data
    simple_gbpdistro = {'release-name': 'foorte',
                        'repositories': {},
                        'type': 'gbp'}
    targets = {'foorte': ['lucid', 'oneiric']}
    # make sure our sample files work for the above checks before
    # proceeding to real data
    rosdep_data = gbprepo_to_rosdep_data(simple_gbpdistro, targets)
    assert rosdep_data is not None
    assert {} == rosdep_data

    gbpdistro_data = {'release-name': 'foorte',
                      'repositories': {
                          'common_msgs': dict(
                               target='all',
                               url='git://github.com/wg-debs/common_msgs.git',
                               packages={ 'foo': 'subdir/foo', 'bar': 'subdir/bar' }),
                          'gazebo': dict(
                               target=['lucid', 'natty'],
                               url='git://github.com/wg-debs/gazebo.git'),
                          'foo-bar': dict(
                               target=['precise'],
                               url='git://github.com/wg-debs/gazebo.git',
                               packages={ 'foo-bar': None }),
                          },
                      'type': 'gbp',
                      }

    rosdep_data = gbprepo_to_rosdep_data(gbpdistro_data, targets)
    for k in ['foo', 'bar', 'gazebo', 'foo-bar']:
        assert k in rosdep_data, k

    # all targets and name transform
    # These are from the 'common_msgs' repo above.
    pkgs = ['foo', 'bar']
    v = 'ros-foorte-%s'
    for pkg in pkgs:
        for p in ['lucid', 'oneiric']:
            rule = rosdep_data[pkg]['ubuntu'][p]
            assert rule['apt']['packages'] == [v % pkg], rule['apt']['packages']
        for p in ['maverick', 'natty']:
            assert p not in rosdep_data[k]['ubuntu']

    # target overrides
    pkg = 'gazebo'
    v = 'ros-foorte-gazebo'
    for p in ['lucid', 'natty']:
        rule = rosdep_data[pkg]['ubuntu'][p]
        assert rule['apt']['packages'] == [v], rule['apt']['packages']
    for p in ['oneiric', 'precise']:
        assert p not in rosdep_data[pkg]['ubuntu']

    # target overrides
    # These are from the 'foo-bar' repo above.
    v = 'ros-foorte-foo-bar'
    for pkg in ['foo-bar']:
        for p in ['precise']:
            rule = rosdep_data[pkg]['ubuntu'][p]
            assert rule['apt']['packages'] == [v], rule['apt']['packages']
        for p in ['oneiric', 'natty', 'lucid']:
            assert p not in rosdep_data[pkg]['ubuntu']


def test_get_owner_name_homebrew():
    from rosdep2.gbpdistro_support import get_owner_name
    empty_url = ''
    assert get_owner_name(empty_url) == 'ros', 'url: ' + empty_url
    https_test_url = 'https://github.com/' \
                    + 'ros/rosdistro/raw/master/releases/fuerte.yaml'
    assert get_owner_name(https_test_url) == 'ros', 'url: ' + https_test_url
    user_test_url = 'https://github.com/' \
                    + 'zklapow/rosdistro/raw/master/releases/fuerte.yaml'
    assert get_owner_name(user_test_url) == 'zklapow', 'url: ' + user_test_url
    non_github_url = 'https://ros.org/files/releases/fuerte.yaml'
    assert get_owner_name(non_github_url) == 'ros', 'url: ' + non_github_url

