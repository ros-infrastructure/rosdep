# Software License Agreement (BSD License)
#
# Copyright (c) 2016, Mike Purvis
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above
#    copyright notice, this list of conditions and the following
#    disclaimer in the documentation and/or other materials provided
#    with the distribution.
#  * Neither the name of Open Source Robotics Foundation, Inc. nor
#    the names of its contributors may be used to endorse or promote
#    products derived from this software without specific prior
#    written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import yaml

from rosinstall_generator.distro import generate_rosinstall, get_package_names
from rosdistro.distribution_file import DistributionFile


def _get_test_dist():
    test_dist_yaml = '''
      repositories:
        riverdale:
          release:
            packages:
            - archie
            - betty
            - veronica
            tags:
              release: release/indigo/{package}/{version}
            url: https://example.com/riverdale-release.git
            version: 1.2.3-0
      type: distribution
      version: 2
    '''
    return DistributionFile('test', yaml.load(test_dist_yaml))


def test_get_package_names():
    d = _get_test_dist()
    assert set(get_package_names(d)[0]) == set(['archie', 'betty', 'veronica'])

    d.repositories['riverdale'].release_repository.version = None
    assert set(get_package_names(d)[1]) == set(['archie', 'betty', 'veronica'])


def test_generate_git():
    d = _get_test_dist()
    r = generate_rosinstall(d, ['betty'])[0]
    assert r['git']['local-name'] == 'riverdale/betty'
    assert r['git']['version'] == 'release/indigo/betty/1.2.3-0'
    assert r['git']['uri'] == 'https://example.com/riverdale-release.git'

    r = generate_rosinstall(d, ['betty'], flat=True)[0]
    assert r['git']['local-name'] == 'betty'


def test_generate_tar():
    d = _get_test_dist()

    r = generate_rosinstall(d, ['archie'], tar=True)[0]
    assert 'tar' not in r

    d.repositories['riverdale'].release_repository.url = 'https://github.com/example/riverdale-release.git'
    r = generate_rosinstall(d, ['archie'], tar=True)[0]
    assert r['tar']['uri'] == 'https://github.com/example/riverdale-release/archive/release/indigo/archie/1.2.3-0.tar.gz'

    d.repositories['riverdale'].release_repository.url = 'https://bitbucket.org/example/riverdale-release.git'
    r = generate_rosinstall(d, ['archie'], tar=True)[0]
    assert r['tar']['uri'] == 'https://bitbucket.org/example/riverdale-release/get/release/indigo/archie/1.2.3-0.tar.gz'

    d.repositories['riverdale'].release_repository.url = 'https://gitlab.example.com/example/riverdale-release.git'
    r = generate_rosinstall(d, ['archie'], tar=True)[0]
    assert r['tar']['uri'] == 'https://gitlab.example.com/example/riverdale-release/repository/archive.tar.gz?ref=release/indigo/archie/1.2.3-0'


def test_generate_tar_from_ssh():
    d = _get_test_dist()
    d.repositories['riverdale'].release_repository.url = 'git@gitlab.example.com:example/riverdale-release.git'
    r = generate_rosinstall(d, ['archie'], tar=True)[0]
    assert r['tar']['uri'] == 'https://gitlab.example.com/example/riverdale-release/repository/archive.tar.gz?ref=release/indigo/archie/1.2.3-0'
