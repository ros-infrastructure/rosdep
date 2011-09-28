# Copyright (c) 2011, Willow Garage, Inc.
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

# Author Ken Conley/kwc@willowgarage.com

import os
import traceback
import yaml
from mock import Mock, patch

def get_test_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), 'source'))

def _subtest_rep112_rdmanifest(resolved):
    test_dir = get_test_dir()
    path = os.path.join(test_dir, 'rep112-example.rdmanifest')
    manifest = yaml.load(open(path))

    assert resolved.manifest == manifest
    assert resolved.manifest_url == path
    assert resolved.install_command == """#!/bin/bash
set -o errexit
mkdir -p build
cd build
cmake ..
make
echo "About to run checkinstall make install"
sudo checkinstall -y --nodoc --pkgname=yaml-cpp-sourcedep make install
""", resolved.install_command
    expected = """#!/bin/bash
dpkg-query -W -f='${Package} ${Status}\\n' yaml-cpp-sourcedep | awk '{\\
if ($4 =="installed")
  exit 0
else
  print "yaml-cpp-sourcedep not installed"
  exit 1}'
"""
    assert resolved.check_presence_command == expected, "\n[%s]\n[%s]"%(resolved.check_presence_command, expected)

    assert len(resolved.check_presence_command) == len(expected), "%s %s"%(len(resolved.check_presence_command), len(expected))

    assert resolved.exec_path == 'yaml-cpp-0.2.5'
    assert resolved.tarball == 'https://kforge.ros.org/rosrelease/viewvc/sourcedeps/yaml-cpp/yaml-cpp-0.2.5.tar.gz'
    assert resolved.alternate_tarball == None
    assert resolved.tarball_md5sum == 'b17dc36055cd2259c88b2602601415d9'

def test_SourceInstall():
    from rosdep2.platforms.source import InvalidRdmanifest, SourceInstall

    #tripwire
    SourceInstall()

    # test unpacking of dict
    manifest = {
        'md5sum': 'fake-md5',
        'exec-path': '/path',
        'install-script': 'echo hello',
        'check-presence-script': 'hello there',
        'uri': 'http://ros.org/',
        'alternate-uri': 'http://turtlebot.com/',
        'depends': ['foo', 'bar'],
        }
    resolved = SourceInstall.from_manifest(manifest, 'fake-url')
    assert resolved.manifest == manifest
    assert resolved.manifest_url == 'fake-url'
    assert resolved.install_command == 'echo hello'
    assert resolved.check_presence_command == 'hello there'
    assert resolved.exec_path == '/path'
    assert resolved.tarball == 'http://ros.org/'
    assert resolved.alternate_tarball == 'http://turtlebot.com/'
    assert resolved.tarball_md5sum == 'fake-md5'

    test_dir = get_test_dir()
    path = os.path.join(test_dir, 'rep112-example.rdmanifest')
    manifest = yaml.load(open(path))
    resolved = SourceInstall.from_manifest(manifest, path)
    _subtest_rep112_rdmanifest(resolved)

    #TODO: test depends

    # test with bad dicts
    manifest = {
        'md5sum': 'fake-md5',
        'exec-path': '/path',
        'install-script': 'echo hello',
        'check-presence-script': 'hello there',
        'alternate-uri': 'http://turtlebot.com/',
        'depends': ['foo', 'bar'],
        }
    # uri is required
    try:
        SourceInstall.from_manifest(manifest, 'foo')
        assert False, "should have raised"
    except InvalidRdmanifest as e:
        pass
    
    # test defaults
    manifest = dict(uri='http://ros.org/')
    resolved = SourceInstall.from_manifest(manifest, 'foo')
    assert resolved.exec_path == '.'
    assert resolved.install_command == ''
    assert resolved.check_presence_command == ''    
    assert resolved.alternate_tarball is None
    assert resolved.tarball_md5sum is None

def test_SourceInstaller():
    from rosdep2.platforms.source import SourceInstaller, InvalidRdmanifest
    test_dir = get_test_dir()

    rosdep_args = {
        'uri': 'todo',
        'md5sum': 'todo',
        }
    # TODO: download rep 112 rdmanifest from URL
    if 0:
        resolved = installer.resolve(rosdep_args)
        _subtest_rep112_rdmanifest(resolved)
        # test again to activate caching
        resolved = installer.resolve(rosdep_args)
        _subtest_rep112_rdmanifest(resolved)
        
def test_load_rdmanifest():
    from rosdep2.platforms.source import load_rdmanifest, InvalidRdmanifest
    # load_rdmanifest is just a YAML unmarshaller with an exception change
    assert 'str' == load_rdmanifest('str')
    assert {'a': 'b'} == load_rdmanifest('{a: b}')

    try:
        load_rdmanifest(';lkajsdf;klj ;l: a;kljdf;: asdf\n ;asdfl;kj')
        assert False, "should have raised"
    except InvalidRdmanifest as e:
        pass
    

REP112_MD5SUM = 'af0dc0e2d0c0c3181dd7670c4147f155'
def test_get_file_hash():
    from rosdep2.platforms.source import get_file_hash
    path = os.path.join(get_test_dir(), 'rep112-example.rdmanifest')
    assert REP112_MD5SUM == get_file_hash(path)
    
def test_fetch_file():
    test_dir = get_test_dir()
    with open(os.path.join(test_dir, 'rep112-example.rdmanifest')) as f:
        expected = f.read()

    from rosdep2.platforms.source import fetch_file
    url = 'https://kforge.ros.org/rosrelease/rosdep/raw-file/931b030d6b3b/test/source/rep112-example.rdmanifest'
    contents, error = fetch_file(url, REP112_MD5SUM)
    assert not error
    assert contents == expected

    contents, error = fetch_file(url, 'badmd5')
    assert bool(error), "should have errored"
    assert not contents

    contents, error = fetch_file('http://badhostname.willowgarage.com', 'md5sum')
    assert not contents
    assert bool(error), "should have errored"
    
def test_download_rdmanifest():
    test_dir = get_test_dir()
    with open(os.path.join(test_dir, 'rep112-example.rdmanifest')) as f:
        expected = yaml.load(f)

    from rosdep2.platforms.source import download_rdmanifest, DownloadFailed
    url = 'https://kforge.ros.org/rosrelease/rosdep/raw-file/931b030d6b3b/test/source/rep112-example.rdmanifest'
    contents, download_url = download_rdmanifest(url, REP112_MD5SUM)
    assert contents == expected
    assert download_url == url

    # test alt_url
    contents, download_url = download_rdmanifest('http://badhostname.willowgarage.com/', REP112_MD5SUM, alt_url=url)
    assert contents == expected
    assert download_url == url

    # test md5sum validate
    try:
        contents, error = download_rdmanifest(url, 'badmd5')
        assert False, "should have errored"
    except DownloadFailed:
        pass

    # test download verify
    try:
        contents, error = download_rdmanifest('http://badhostname.willowgarage.com', 'fakemd5')
        assert False, "should have errored"
    except DownloadFailed:
        pass

    
