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
from mock import patch, Mock

def get_test_dir():
    # not used yet
    return os.path.abspath(os.path.join(os.path.dirname(__file__), 'redhat'))

def test_rpm_detect():
    from rosdep2.platforms.redhat import rpm_detect

    m = Mock()
    m.return_value = ''

    val = rpm_detect([], exec_fn=m)
    assert val == [], val

    val = rpm_detect(['tinyxml-dev'], exec_fn=m)
    assert val == [], val

def test_DnfInstaller():
    from rosdep2.platforms.redhat import DnfInstaller

    @patch.object(DnfInstaller, 'get_packages_to_install')
    def test(mock_method):
        installer = DnfInstaller()
        mock_method.return_value = []
        assert [] == installer.get_install_command(['fake'])

        # no interactive option with YUM
        mock_method.return_value = ['a', 'b']
        expected = [['sudo', '-H', 'dnf', '--assumeyes', '--quiet', 'install', 'a', 'b']]
        val = installer.get_install_command(['whatever'], interactive=False, quiet=True)
        assert val == expected, val + expected
        expected = [['sudo', '-H', 'dnf', '--quiet', 'install', 'a', 'b']]
        val = installer.get_install_command(['whatever'], interactive=True, quiet=True)
        assert val == expected, val + expected
        expected = [['sudo', '-H', 'dnf', '--assumeyes', 'install', 'a', 'b']]
        val = installer.get_install_command(['whatever'], interactive=False, quiet=False)
        assert val == expected, val + expected
        expected = [['sudo', '-H', 'dnf', 'install', 'a', 'b']]
        val = installer.get_install_command(['whatever'], interactive=True, quiet=False)
        assert val == expected, val + expected
    try:
        test()
    except AssertionError:
        traceback.print_exc()
        raise

def test_YumInstaller():
    from rosdep2.platforms.redhat import YumInstaller

    @patch.object(YumInstaller, 'get_packages_to_install')
    def test(mock_method):
        installer = YumInstaller()
        mock_method.return_value = []
        assert [] == installer.get_install_command(['fake'])

        # no interactive option with YUM
        mock_method.return_value = ['a', 'b']
        expected = [['sudo', '-H', 'yum', '--assumeyes', '--quiet', '--skip-broken', 'install', 'a', 'b']]
        val = installer.get_install_command(['whatever'], interactive=False, quiet=True)
        assert val == expected, val + expected
        expected = [['sudo', '-H', 'yum', '--quiet', '--skip-broken', 'install', 'a', 'b']]
        val = installer.get_install_command(['whatever'], interactive=True, quiet=True)
        assert val == expected, val + expected
        expected = [['sudo', '-H', 'yum', '--assumeyes', '--skip-broken', 'install', 'a', 'b']]
        val = installer.get_install_command(['whatever'], interactive=False, quiet=False)
        assert val == expected, val + expected
        expected = [['sudo', '-H', 'yum', '--skip-broken', 'install', 'a', 'b']]
        val = installer.get_install_command(['whatever'], interactive=True, quiet=False)
        assert val == expected, val + expected
    try:
        test()
    except AssertionError:
        traceback.print_exc()
        raise

def test_Fedora_variable_installer_key():
    from rosdep2 import InstallerContext
    from rosdep2.platforms import pip, redhat, source
    from rosdep2.platforms.redhat import DNF_INSTALLER, YUM_INSTALLER

    from rospkg.os_detect import OsDetect, OS_FEDORA
    os_detect_mock = Mock(spec=OsDetect)
    os_detect_mock.get_name.return_value = 'fedora'
    os_detect_mock.get_codename.return_value = 'twenty'
    os_detect_mock.get_version.return_value = '21'

    # create our test fixture.  use most of the default toolchain, but
    # replace the apt installer with one that we can have more fun
    # with.  we will do all tests with ubuntu lucid keys -- other
    # tests should cover different resolution cases.
    context = InstallerContext(os_detect_mock)
    pip.register_installers(context)
    redhat.register_installers(context)
    source.register_installers(context)
    redhat.register_platforms(context)

    assert YUM_INSTALLER == context.get_default_os_installer_key(OS_FEDORA)

    os_detect_mock.get_version.return_value = '22'
    assert DNF_INSTALLER == context.get_default_os_installer_key(OS_FEDORA)

def test_Fedora_variable_lookup_key():
    from rosdep2 import InstallerContext
    from rosdep2.platforms import pip, redhat, source
    from rosdep2.platforms.redhat import DNF_INSTALLER, YUM_INSTALLER

    from rospkg.os_detect import OsDetect, OS_FEDORA
    os_detect_mock = Mock(spec=OsDetect)
    os_detect_mock.get_name.return_value = 'fedora'
    os_detect_mock.get_codename.return_value = 'heisenbug'
    os_detect_mock.get_version.return_value = '20'

    # create our test fixture.  use most of the default toolchain, but
    # replace the apt installer with one that we can have more fun
    # with.  we will do all tests with ubuntu lucid keys -- other
    # tests should cover different resolution cases.
    context = InstallerContext(os_detect_mock)
    pip.register_installers(context)
    redhat.register_installers(context)
    source.register_installers(context)
    redhat.register_platforms(context)

    assert ('fedora', 'heisenbug') == context.get_os_name_and_version()

    os_detect_mock.get_codename.return_value = 'twenty'
    os_detect_mock.get_version.return_value = '21'
    assert (OS_FEDORA, '21') == context.get_os_name_and_version()
