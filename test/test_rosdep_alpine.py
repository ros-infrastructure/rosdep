# Copyright (c) 2018, SEQSENSE, Inc.
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

# Author Atsushi Watanabe/atsushi.w@ieee.org

import os
import traceback
try:
    from unittest.mock import Mock, call, patch
except ImportError:
    from mock import Mock, call, patch

import rospkg.os_detect


def get_test_dir():
    # not used yet
    return os.path.abspath(os.path.join(os.path.dirname(__file__), 'alpine'))


def test_apk_detect():
    from rosdep2.platforms.alpine import apk_detect

    m = Mock(return_value='')
    expected = []
    val = apk_detect([], exec_fn=m)
    assert val == expected, 'Result was: %s' % val
    m.assert_not_called()

    m = Mock(return_value='')
    expected = []
    val = apk_detect(['a'], exec_fn=m)
    assert val == expected, 'Result was: %s' % val
    m.assert_has_calls([
        call(['apk', 'info', '--installed', 'a']),
        call(['apk', 'info', '--installed', '--replaces', 'a']),
    ])

    m = Mock(side_effect=[
        '\n'.join(['a', 'b']),
        '',
    ])
    expected = ['a', 'b']
    val = apk_detect(['a', 'b'], exec_fn=m)
    assert val == expected, 'Result was: %s' % val
    m.assert_has_calls([
        call(['apk', 'info', '--installed', 'a', 'b']),
        call(['apk', 'info', '--installed', '--replaces', 'a', 'b']),
    ])

    # Packages installed by alias names should be resolved.
    m = Mock(side_effect=[
        '\n'.join(['origin-pkg1', 'origin-pkg2']),
        '\n'.join([
            'origin-pkg1=0.0.0-r0 replaces:',
            'alias-pkg1',
            '',
            'origin-pkg2=1.1.1-r1 replaces:',
            'alias-pkg2',
            '',
        ]),
    ])
    expected = ['origin-pkg1', 'origin-pkg2', 'alias-pkg1', 'alias-pkg2']
    val = apk_detect(['alias-pkg1', 'alias-pkg2'], exec_fn=m)
    assert val == expected, 'Result was: %s' % val
    m.assert_has_calls([
        call(['apk', 'info', '--installed', 'alias-pkg1', 'alias-pkg2']),
        call(['apk', 'info', '--installed', '--replaces', 'alias-pkg1', 'alias-pkg2']),
    ])


def test_ApkInstaller():
    from rosdep2.platforms.alpine import ApkInstaller

    @patch.object(ApkInstaller, 'get_packages_to_install')
    def test(expected_prefix, mock_method):
        installer = ApkInstaller()
        mock_method.return_value = []
        assert [] == installer.get_install_command(['nonexistingfakepackage'])

        mock_method.return_value = ['a-dev', 'b-dev']

        expected = [expected_prefix + ['apk', 'add', 'a-dev', 'b-dev']]
        val = installer.get_install_command(['notused'], interactive=False, quiet=False)
        assert val == expected, 'Result was: %s' % val

        expected = [expected_prefix + ['apk', 'add', '--interactive', 'a-dev', 'b-dev']]
        val = installer.get_install_command(['notused'], interactive=True, quiet=False)
        assert val == expected, 'Result was: %s' % val

        expected = [expected_prefix + ['apk', 'add', '--quiet', 'a-dev', 'b-dev']]
        val = installer.get_install_command(['notused'], interactive=False, quiet=True)
        assert val == expected, 'Result was: %s' % val

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
