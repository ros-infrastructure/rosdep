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

# Copied from test_rosdep_suse.py by Author Ken Conley/kwc@willowgarage.com
# Converted to FreeBSD by Trenton Schulz/trentonw@ifi.uio.no

import os
import traceback
from unittest.mock import patch, Mock


def get_test_dir():
    # not used yet
    return os.path.abspath(os.path.join(os.path.dirname(__file__), 'freebsd'))


def test_pkg_detect():
    from rosdep2.platforms.freebsd import pkg_detect

    m = Mock()
    m.return_value = ''

    val = pkg_detect([], exec_fn=m)
    assert val == [], val

    val = pkg_detect(['tinyxml'], exec_fn=m)
    assert val == [], val


def test_PkgInstaller():
    from rosdep2.platforms.freebsd import PkgInstaller

    @patch.object(PkgInstaller, 'get_packages_to_install')
    def test(expected_prefix, mock_method):
        installer = PkgInstaller()
        mock_method.return_value = []
        assert [] == installer.get_install_command(['fake'])

        # no interactive option with YUM
        mock_method.return_value = ['a', 'b']
        expected = [expected_prefix + ['/usr/sbin/pkg', 'install', '-y', 'a', 'b']]
        val = installer.get_install_command(['whatever'], interactive=False)
        assert val == expected, val
        expected = [expected_prefix + ['/usr/sbin/pkg', 'install', '-y', 'a', 'b']]
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
