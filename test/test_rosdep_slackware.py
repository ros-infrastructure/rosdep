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

# Author Nikolay Nikolov/niko.b.nikolov@gmail.com

import os
import traceback
from unittest.mock import Mock, patch

import rospkg.os_detect


def is_slackware():
    return rospkg.os_detect.Slackware().is_os()


def get_test_dir():
    # not used yet
    return os.path.abspath(os.path.join(os.path.dirname(__file__), 'slackware'))


def test_sbotools_available():
    if not is_slackware():
        print('Skipping not Slackware')
        return
    from rosdep2.platforms.slackware import sbotools_available

    original_exists = os.path.exists

    path_overrides = {}

    def mock_path(path):
        if path in path_overrides:
            return path_overrides[path]
        else:
            return original_exists(path)

    m = Mock(side_effect=mock_path)
    os.path.exists = m

    # Test with sbotools missing
    m.reset_mock()
    path_overrides = {}
    path_overrides['/usr/sbin/sboinstall'] = False

    val = sbotools_available()
    assert not val, 'Sbotools should not be available'

    # Test with sbotools installed
    m.reset_mock()
    path_overrides = {}
    path_overrides['/usr/sbin/sboinstall'] = True

    val = sbotools_available()
    assert val, 'Sbotools should be available'

    os.path.exists = original_exists


def test_SbotoolsInstaller():
    if not is_slackware():
        print('Skipping not Slackware')
        return

    from rosdep2.platforms.slackware import SbotoolsInstaller

    @patch.object(SbotoolsInstaller, 'get_packages_to_install')
    def test(expected_prefix, mock_method):
        installer = SbotoolsInstaller()
        mock_method.return_value = []
        assert [] == installer.get_install_command(['fake'])

        mock_method.return_value = ['a', 'b']

        expected = [expected_prefix + ['sboinstall', '-r', 'a'],
                    expected_prefix + ['sboinstall', '-r', 'b']]
        val = installer.get_install_command(['whatever'], interactive=False)
        assert val == expected, val

        expected = [expected_prefix + ['sboinstall', 'a'],
                    expected_prefix + ['sboinstall', 'b']]
        val = installer.get_install_command(['whatever'], interactive=True)
        assert val == expected, val

    try:
        with patch('rosdep2.installers.os.geteuid', return_value=1):
            test(['sudo', '-H'])
        with patch('rosdep2.installers.os.geteuid', return_value=0):
            test([])
    except AssertionError:
        traceback.print_exc()
        raise


def test_slackpkg_available():
    if not is_slackware():
        print('Skipping not Slackware')
        return
    from rosdep2.platforms.slackware import slackpkg_available

    original_exists = os.path.exists

    path_overrides = {}

    def mock_path(path):
        if path in path_overrides:
            return path_overrides[path]
        else:
            return original_exists(path)

    m = Mock(side_effect=mock_path)
    os.path.exists = m

    # Test with sbotools missing
    m.reset_mock()
    path_overrides = {}
    path_overrides['/usr/sbin/slackpkg'] = False

    val = slackpkg_available()
    assert not val, 'Slackpkg should not be available'

    # Test with sbotools installed
    m.reset_mock()
    path_overrides = {}
    path_overrides['/usr/sbin/slackpkg'] = True

    val = slackpkg_available()
    assert val, 'Slackpkg should be available'

    os.path.exists = original_exists


def test_SlackpkgInstaller():
    if not is_slackware():
        print('Skipping not Slackware')
        return

    from rosdep2.platforms.slackware import SlackpkgInstaller

    @patch.object(SlackpkgInstaller, 'get_packages_to_install')
    def test(expected_prefix, mock_method):
        installer = SlackpkgInstaller()
        mock_method.return_value = []
        assert [] == installer.get_install_command(['fake'])

        mock_method.return_value = ['a', 'b']

        expected = [expected_prefix + ['slackpkg', 'install', 'a'],
                    expected_prefix + ['slackpkg', 'install', 'b']]
        val = installer.get_install_command(['whatever'], interactive=False)
        assert val == expected, val

        expected = [expected_prefix + ['slackpkg', 'install', 'a'],
                    expected_prefix + ['slackpkg', 'install', 'b']]
        val = installer.get_install_command(['whatever'], interactive=True)
        assert val == expected, val

    try:
        with patch('rosdep2.installers.os.geteuid', return_value=1):
            test(['sudo', '-H'])
        with patch('rosdep2.installers.os.geteuid', return_value=0):
            test([])
    except AssertionError:
        traceback.print_exc()
        raise
