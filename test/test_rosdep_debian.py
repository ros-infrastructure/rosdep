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
from mock import Mock, patch, call


def get_test_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), 'debian'))


def test_dpkg_detect():
    from rosdep2.platforms.debian import dpkg_detect

    with patch('rosdep2.platforms.debian.read_stdout') as mock_read_stdout:
        mock_read_stdout.side_effect = [('', ''), '']
        val = dpkg_detect([])
        assert val == [], val
        assert mock_read_stdout.call_count == 2
        assert mock_read_stdout.call_args_list[0] == call(['dpkg-query', '-W', "-f='${Package} ${Status}\n'"], True)
        assert mock_read_stdout.call_args_list[1] == call(['apt-cache', 'showpkg'])

    with patch('rosdep2.platforms.debian.read_stdout') as mock_read_stdout:
        mock_read_stdout.side_effect = [('', ''), '']
        val = dpkg_detect(['tinyxml-dev'])
        assert val == [], val
        assert mock_read_stdout.call_count == 2
        assert mock_read_stdout.call_args_list[0] == call(['dpkg-query', '-W', "-f='${Package} ${Status}\n'",
                                                           'tinyxml-dev'], True)
        assert mock_read_stdout.call_args_list[1] == call(['apt-cache', 'showpkg', 'tinyxml-dev'])

    with open(os.path.join(get_test_dir(), 'dpkg-python-apt'), 'r') as f:
        dpkg_python_apt_test_content = f.read()

    with patch('rosdep2.platforms.debian.read_stdout') as mock_read_stdout:
        mock_read_stdout.side_effect = [(dpkg_python_apt_test_content, ''), '']
        val = dpkg_detect(['apt', 'tinyxml-dev', 'python'])
        assert val == ['apt', 'python'], val
        assert mock_read_stdout.call_count == 2
        print(mock_read_stdout.call_args_list[0])
        assert mock_read_stdout.call_args_list[1] == call(['apt-cache', 'showpkg', 'tinyxml-dev'])

    # test version lock code (should be filtered out w/o validation)
    with patch('rosdep2.platforms.debian.read_stdout') as mock_read_stdout:
        mock_read_stdout.side_effect = [(dpkg_python_apt_test_content, ''), '']
        val = dpkg_detect(['apt=1.8', 'tinyxml-dev', 'python=2.7'])
        assert val == ['apt=1.8', 'python=2.7'], val
        assert mock_read_stdout.call_count == 2
        assert mock_read_stdout.call_args_list[1] == call(['apt-cache', 'showpkg', 'tinyxml-dev'])


def test_read_apt_cache_showpkg():
    from rosdep2.platforms.debian import _read_apt_cache_showpkg

    m = Mock()
    with open(os.path.join(get_test_dir(), 'showpkg-curl-wget-libcurl-dev'), 'r') as f:
        m.return_value = f.read()
    pkgs = ['curl', 'wget', '_not_existing', 'libcurl-dev', 'ros-kinetic-rc-genicam-api']
    results = list(_read_apt_cache_showpkg(pkgs, exec_fn=m))
    assert len(results) == len(pkgs), results

    package, virtual, providers = results[0]
    assert package == 'curl', package
    assert not virtual
    assert providers is None, providers

    package, virtual, providers = results[1]
    assert package == 'wget', package
    assert not virtual
    assert providers is None, providers

    package, virtual, providers = results[2]
    assert package == '_not_existing', package
    assert not virtual
    assert providers is None, providers

    package, virtual, providers = results[3]
    assert package == 'libcurl-dev', package
    assert virtual, providers

    package, virtual, providers = results[4]
    assert package == 'ros-kinetic-rc-genicam-api', package
    assert not virtual
    assert providers is None, providers


def test_AptInstaller():
    from rosdep2.platforms.debian import AptInstaller

    @patch('rosdep2.platforms.debian.read_stdout')
    @patch.object(AptInstaller, 'get_packages_to_install')
    def test(mock_get_packages_to_install, mock_read_stdout):
        installer = AptInstaller()
        mock_get_packages_to_install.return_value = []
        mock_read_stdout.return_value = ''
        assert [] == installer.get_install_command(['fake'])

        mock_get_packages_to_install.return_value = ['a', 'b']
        expected = [['sudo', '-H', 'apt-get', 'install', '-y', 'a'],
                    ['sudo', '-H', 'apt-get', 'install', '-y', 'b']]
        val = installer.get_install_command(['whatever'], interactive=False)
        print('VAL', val)
        assert val == expected, val
        expected = [['sudo', '-H', 'apt-get', 'install', 'a'],
                    ['sudo', '-H', 'apt-get', 'install', 'b']]
        val = installer.get_install_command(['whatever'], interactive=True)
        assert val == expected, val
    try:
        test()
    except AssertionError:
        traceback.print_exc()
        raise
