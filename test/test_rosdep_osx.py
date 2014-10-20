# -*- coding: utf-8 -*-

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

from mock import call
from mock import Mock
from mock import patch


def get_test_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), 'osx'))


def is_port_installed_tripwire():
    # don't know the correct answer, but make sure this does not throw
    from rosdep2.platforms.osx import is_port_installed
    assert is_port_installed() in [True, False]


def is_brew_installed_tripwire():
    # don't know the correct answer, but make sure this does not throw
    from rosdep2.platforms.osx import is_brew_installed
    assert is_brew_installed() in [True, False]


def make_resolutions(package_list):
    from rosdep2.platforms.osx import HomebrewResolution
    return list(map(lambda pkg: HomebrewResolution(pkg, [], []), package_list))


def make_resolutions_options(package_list):
    from rosdep2.platforms.osx import HomebrewResolution
    return list(map(lambda pkg: HomebrewResolution(pkg[0], pkg[1], pkg[2]), package_list))


def brew_command(command):
    if command[1] == "list":
        with open(os.path.join(get_test_dir(), 'brew-list-output'), 'r') as f:
            return f.read()
    elif command[1] == "info":
        pkg = command[2]
        with open(os.path.join(get_test_dir(), 'brew-info-output'), 'r') as f:
            output = f.readlines()
        for line in output:
            res = line.split(":", 1)
            if res[0] == pkg:
                return res[1]
    return ''


def test_brew_detect():
    from rosdep2.platforms.osx import brew_detect

    m = Mock()
    m.return_value = ''
    val = brew_detect([], exec_fn=m)
    assert val == [], val

    m = Mock()
    m.return_value = ''
    val = brew_detect(make_resolutions(['tinyxml']), exec_fn=m)
    assert val == [], val
    # make sure our test harness is based on the same implementation
    m.assert_called_with(['brew', 'list'])
    assert m.call_args_list == [call(['brew', 'list'])], m.call_args_list

    m = Mock()
    m.side_effect = brew_command
    val = brew_detect(make_resolutions(['apt', 'subversion', 'python', 'bazaar']), exec_fn=m)
    # make sure it preserves order
    expected = make_resolutions(['subversion', 'bazaar'])
    assert set(val) == set(expected), val
    assert val == expected, val
    assert len(val) == len(set(val)), val


def test_HomebrewInstaller():
    from rosdep2.platforms.osx import HomebrewInstaller

    @patch('rosdep2.platforms.osx.is_brew_installed')
    @patch.object(HomebrewInstaller, 'remove_duplicate_dependencies')
    @patch.object(HomebrewInstaller, 'get_packages_to_install')
    def test(mock_get_packages_to_install, mock_remove_duplicate_dependencies, mock_brew_installed):
        mock_brew_installed.return_value = True

        installer = HomebrewInstaller()
        mock_get_packages_to_install.return_value = []
        mock_remove_duplicate_dependencies.return_value = mock_get_packages_to_install.return_value
        assert [] == installer.get_install_command(make_resolutions(['fake']))

        mock_get_packages_to_install.return_value = make_resolutions(['subversion', 'bazaar'])
        mock_remove_duplicate_dependencies.return_value = mock_get_packages_to_install.return_value
        expected = [['brew', 'install', 'subversion'],
                    ['brew', 'install', 'bazaar']]
        # brew is always non-interactive
        for interactive in [True, False]:
            val = installer.get_install_command(['whatever'], interactive=interactive)
            assert val == expected, val

        expected = [['brew', 'uninstall', '--force', 'subversion'],
                    ['brew', 'install', 'subversion'],
                    ['brew', 'uninstall', '--force', 'bazaar'],
                    ['brew', 'install', 'bazaar']]
        val = installer.get_install_command(['whatever'], reinstall=True)
        assert val == expected, val

        mock_get_packages_to_install.return_value = make_resolutions_options(
            [('subversion', ['foo', 'bar'], ['baz']), ('bazaar', [], ['--with-quux'])])
        mock_remove_duplicate_dependencies.return_value = mock_get_packages_to_install.return_value
        expected = [['brew', 'install', 'subversion', 'foo', 'bar', 'baz'],
                    ['brew', 'install', 'bazaar', '--with-quux']]
        val = installer.get_install_command(['whatever'])
        assert val == expected, val

        try:
            mock_get_packages_to_install.return_value = eval("make_resolutions_options([('subversion', [u'f´´ßß', u'öäö'], []), (u'bazaar', [], [u'tüü'])])")
        except SyntaxError:
            # Python 3.2, u'...' is not allowed, but string literals are unicode
            mock_get_packages_to_install.return_value = make_resolutions_options(
                [('subversion', ['f´´ßß', 'öäö'], []), ('bazaar', [], ["tüü"])])
        mock_remove_duplicate_dependencies.return_value = mock_get_packages_to_install.return_value
        try:
            expected = eval("[['brew', 'install', 'subversion', u'f´´ßß', u'öäö'], ['brew', 'install', 'bazaar', u'tüü']]")
        except SyntaxError:
            # Python 3.2, u'...' is not allowed, but string literals are unicode
            expected = [['brew', 'install', 'subversion', 'f´´ßß', 'öäö'],
                        ['brew', 'install', 'bazaar', "tüü"]]
        val = installer.get_install_command(['whatever'])
        assert val == expected, val
    try:
        test()
    except AssertionError:
        traceback.print_exc()
        raise
