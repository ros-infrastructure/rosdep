# Copyright (c) 2011, Willow Garage, Inc.
# Copyright (c) 2019, Kei Okada
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
# Author Kei Okada/kei.okada@gmail.com

import os
import traceback
from unittest.mock import Mock, patch


def get_test_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), 'npm'))


def test_npm_detect():
    from rosdep2.platforms.npm import NpmInstaller
    installer = NpmInstaller()
    npm_detect = installer.npm_detect

    m = Mock()

    # test behavior with empty freeze
    m.return_value = ''
    val = npm_detect([], exec_fn=m)
    assert val == [], val

    val = npm_detect(['rosnodejs'], exec_fn=m)
    assert val == [], val

    # read list output into mock exec_fn
    with open(os.path.join(get_test_dir(), 'list_output'), 'r') as f:
        m.return_value = f.read()
    val = npm_detect(['rosnodejs'], exec_fn=m)
    assert val == ['rosnodejs'], val

    val = npm_detect(['argparse', 'fakito', 'rosnodejs'], exec_fn=m)
    assert val == ['rosnodejs', 'argparse'], val


def test_NpmInstaller_get_depends():
    # make sure NpmInstaller supports depends
    from rosdep2.platforms.npm import NpmInstaller
    installer = NpmInstaller()
    assert ['foo'] == installer.get_depends(dict(depends=['foo']))


def test_NpmInstaller():
    from rosdep2 import InstallFailed
    from rosdep2.platforms.npm import NpmInstaller

    @patch('rosdep2.platforms.npm.is_npm_installed')
    def test_no_npm(mock_method):
        mock_method.return_value = False
        try:
            installer = NpmInstaller()
            installer.get_install_command(['whatever'])
            assert False, 'should have raised'
        except InstallFailed:
            pass

    test_no_npm()

    @patch('rosdep2.platforms.npm.is_npm_installed')
    @patch.object(NpmInstaller, 'get_packages_to_install')
    def test(expected_prefix, mock_method, mock_is_npm_installed):
        mock_is_npm_installed.return_value = True
        installer = NpmInstaller()
        mock_method.return_value = []
        assert [] == installer.get_install_command(['fake'])

        # no interactive option with NPM
        mock_method.return_value = ['a', 'b']
        expected = [expected_prefix + ['npm', 'install', '-g', 'a'],
                    expected_prefix + ['npm', 'install', '-g', 'b']]
        val = installer.get_install_command(['whatever'], interactive=False)
        assert val == expected, val
        expected = [expected_prefix + ['npm', 'install', '-g', 'a'],
                    expected_prefix + ['npm', 'install', '-g', 'b']]
        val = installer.get_install_command(['whatever'], interactive=True)
        assert val == expected, val

        # unset as_root option with NPM
        installer.as_root = False
        expected = [['npm', 'install', 'a'],
                    ['npm', 'install', 'b']]
        val = installer.get_install_command(['whatever'], interactive=False)
        assert val == expected, val
        expected = [['npm', 'install', 'a'],
                    ['npm', 'install', 'b']]
        val = installer.get_install_command(['whatever'], interactive=True)
        assert val == expected, val
    try:
        if hasattr(os, 'geteuid'):
            with patch('rosdep2.installers.os.geteuid', return_value=1):
                test(['sudo', '-H'])
            with patch('rosdep2.installers.os.geteuid', return_value=0):
                test([])
        else:
            test([])
    except AssertionError:
        traceback.print_exc()
        raise
