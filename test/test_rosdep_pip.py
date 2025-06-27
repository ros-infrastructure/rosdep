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
import sys
import traceback
from unittest.mock import Mock, patch


def get_test_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), 'pip'))


def test_pip_detect():
    from rosdep2.platforms.pip import pip_detect

    m = Mock()

    # test behavior with empty freeze
    m.return_value = ''
    val = pip_detect([], exec_fn=m)
    assert val == [], val

    val = pip_detect(['paramiko'], exec_fn=m)
    assert val == [], val

    # read freeze output into mock exec_fn
    with open(os.path.join(get_test_dir(), 'freeze_output'), 'r') as f:
        m.return_value = f.read()
    val = pip_detect(['paramiko'], exec_fn=m)
    assert val == ['paramiko'], val

    val = pip_detect(['paramiko', 'fakito', 'pycrypto'], exec_fn=m)
    assert val == ['paramiko', 'pycrypto'], val


def test_PipInstaller_get_depends():
    # make sure PipInstaller supports depends
    from rosdep2.platforms.pip import PipInstaller
    installer = PipInstaller()
    assert ['foo'] == installer.get_depends(dict(depends=['foo']))


@patch('rosdep2.platforms.pip.externally_managed_installable')
def test_PipInstaller_handles_externally_managed_environment(externally_managed_installable):
    from rosdep2 import InstallFailed
    from rosdep2.platforms.pip import EXTERNALLY_MANAGED_EXPLAINER, PipInstaller

    externally_managed_installable.return_value = False
    installer = PipInstaller()
    try:
        installer.get_install_command(['whatever'])
        assert False, 'should have raised'
    except InstallFailed as e:
        assert e.failures == [('pip', EXTERNALLY_MANAGED_EXPLAINER)]
    externally_managed_installable.return_value = True
    assert installer.get_install_command(['whatever'], interactive=False)


@patch('rosdep2.platforms.pip.sys.version_info', new=(3, 11))
@patch.dict(os.environ, {'PIP_BREAK_SYSTEM_PACKAGES': '0'})
def test_externally_managed_installable():
    from rosdep2.platforms.pip import externally_managed_installable
    assert externally_managed_installable() is False

    @patch('rosdep2.platforms.pip.sys.version_info', new=(3, 10))
    def test_last_exempt_version():
        assert externally_managed_installable()

    @patch.dict(os.environ, {'PIP_BREAK_SYSTEM_PACKAGES': '1'})
    def test_break_system_packages_env_var():
        assert externally_managed_installable()

    from configparser import ConfigParser
    from pathlib import Path

    @patch.object(ConfigParser, 'read')
    @patch.object(ConfigParser, 'getboolean')
    @patch.dict(os.environ, {'XDG_CONFIG_DIRS': '/xdg'})
    def test_xdg_pip_dot_conf(getboolean, read):
        getboolean.return_value = True
        assert externally_managed_installable()
        read.assert_called_once_with(Path('/xdg/pip/pip.conf'))
        getboolean.assert_called_once_with('install', 'break-system-packages', fallback=False)

    @patch.object(ConfigParser, 'read')
    @patch.object(ConfigParser, 'getboolean')
    def test_pip_dot_conf(getboolean, read):
        getboolean.return_value = True
        assert externally_managed_installable()
        read.assert_called_once_with(Path('/etc/pip.conf'))
        getboolean.assert_called_once_with('install', 'break-system-packages', fallback=False)

    test_last_exempt_version()
    test_break_system_packages_env_var()
    test_xdg_pip_dot_conf()
    test_pip_dot_conf()


@patch.dict(os.environ, {'PIP_BREAK_SYSTEM_PACKAGES': '1'})
def test_PipInstaller():
    from rosdep2 import InstallFailed
    from rosdep2.platforms.pip import PipInstaller

    @patch('rosdep2.platforms.pip.get_pip_command')
    def test_no_pip(mock_method):
        mock_method.return_value = None
        try:
            installer = PipInstaller()
            installer.get_install_command(['whatever'])
            assert False, 'should have raised'
        except InstallFailed:
            pass

    test_no_pip()

    @patch('rosdep2.platforms.pip.get_pip_command')
    @patch.object(PipInstaller, 'get_packages_to_install')
    def test(expected_prefix, mock_method, mock_get_pip_command):
        mock_get_pip_command.return_value = ['mock-pip']
        installer = PipInstaller()
        mock_method.return_value = []
        assert [] == installer.get_install_command(['fake'])

        # no interactive option with PIP
        mock_method.return_value = ['a', 'b']
        expected = [expected_prefix + ['mock-pip', 'install', '-U', 'a'],
                    expected_prefix + ['mock-pip', 'install', '-U', 'b']]
        val = installer.get_install_command(['whatever'], interactive=False)
        assert val == expected, val
        expected = [expected_prefix + ['mock-pip', 'install', '-U', 'a'],
                    expected_prefix + ['mock-pip', 'install', '-U', 'b']]
        val = installer.get_install_command(['whatever'], interactive=True)
        assert val == expected, val
    try:
        if hasattr(os, 'geteuid'):
            with patch('rosdep2.installers.os.geteuid', return_value=1):
                test(['sudo', '-H', '--preserve-env=PIP_BREAK_SYSTEM_PACKAGES'])
            with patch('rosdep2.installers.os.geteuid', return_value=0):
                test([])
        else:
            test([])
    except AssertionError:
        traceback.print_exc()
        raise


def test_PipInstaller_get_version_strings():
    from rosdep2.platforms.pip import PipInstaller

    installer = PipInstaller()
    assert installer.get_version_strings()


def test_get_pip_command():
    from rosdep2.platforms.pip import get_pip_command

    # pip2 or pip3
    @patch('rosdep2.platforms.pip.is_cmd_available')
    def test_pip2_or_pip3(mock_is_cmd_available):
        mock_is_cmd_available.return_value = True

        with patch.dict(os.environ, {'ROS_PYTHON_VERSION': '2'}):
            assert ['pip2'] == get_pip_command()

        with patch.dict(os.environ, {'ROS_PYTHON_VERSION': '3'}):
            assert ['pip3'] == get_pip_command()

    # sys.executable (assumes pip is installed)
    @patch('rosdep2.platforms.pip.is_cmd_available')
    def test_sys_executable(mock_is_cmd_available):
        mock_is_cmd_available.return_value = False

        with patch.dict(os.environ, {'ROS_PYTHON_VERSION': str(sys.version[0])}):
            assert [sys.executable, '-m', 'pip'] == get_pip_command()

    # python2 or python3
    def fake_is_cmd_available(cmd):
        if cmd[0] in ['pip2', 'pip3']:
            return False
        return True

    @patch('rosdep2.platforms.pip.is_cmd_available', new=fake_is_cmd_available)
    def test_python2_or_python3(mock_is_cmd_available):

        with patch.dict(os.environ, {'ROS_PYTHON_VERSION': '2'}):
            assert ['python2', '-m', 'pip'] == get_pip_command()

        with patch.dict(os.environ, {'ROS_PYTHON_VERSION': '3'}):
            assert ['python3', '-m', 'pip'] == get_pip_command()
