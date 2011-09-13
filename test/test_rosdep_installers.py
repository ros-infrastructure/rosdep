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

from __future__ import print_function

import os
import sys

def test_InstallerContext_ctor():
    from rosdep.installers import InstallerContext
    from rospkg.os_detect import OsDetect

    context = InstallerContext()
    assert context.get_os_detect() is not None
    assert isinstance(context.get_os_detect(), OsDetect)

    detect = OsDetect()
    context = InstallerContext(detect)
    assert context.get_os_detect() == detect
    assert [] == context.get_installer_keys()
    assert [] == context.get_os_installer_keys('foo')

def test_InstallerContext_installers():
    from rosdep.installers import InstallerContext, Installer
    from rospkg.os_detect import OsDetect
    detect = OsDetect()
    context = InstallerContext(detect)

    key = 'fake-apt'
    try:
        installer = context.get_installer(key)
        assert False, "should have raised: %s"%(installer)
    except KeyError: pass

    class Foo: pass
    # test TypeError on set_installer
    try:
        context.set_installer(key, 1)
        assert False, "should have raised"
    except TypeError: pass
    try:
        context.set_installer(key, Foo)
        assert False, "should have raised"
    except TypeError: pass

    class FakeInstaller(Installer):
        pass
    class FakeInstaller2(Installer):
        pass

    context.set_installer(key, FakeInstaller)
    assert context.get_installer(key) == FakeInstaller
    assert context.get_installer_keys() == [key]

    # repeat with same args
    context.set_installer(key, FakeInstaller)
    assert context.get_installer(key) == FakeInstaller
    assert context.get_installer_keys() == [key]

    # repeat with new installer
    context.set_installer(key, FakeInstaller2)
    assert context.get_installer(key) == FakeInstaller2
    assert context.get_installer_keys() == [key]
    
    # repeat with new key
    key2 = 'fake-port'
    context.set_installer(key2, FakeInstaller2)
    assert context.get_installer(key2) == FakeInstaller2
    assert set(context.get_installer_keys()) == set([key, key2])


def test_InstallerContext_os_installers():
    from rosdep.installers import InstallerContext, Installer
    from rospkg.os_detect import OsDetect
    detect = OsDetect()
    context = InstallerContext(detect)

    os_key = 'ubuntu'
    assert [] == context.get_os_installer_keys(os_key)
    assert None == context.get_default_os_installer_key(os_key)
    try:
        context.add_os_installer_key(os_key, 'fake-key')
        assert False, "should have raised"
    except KeyError: pass
    
    installer_key1 = 'fake1'
    installer_key2 = 'fake2'
    class FakeInstaller(Installer):
        pass
    class FakeInstaller2(Installer):
        pass
    context.set_installer(installer_key1, FakeInstaller)
    context.set_installer(installer_key2, FakeInstaller2)
