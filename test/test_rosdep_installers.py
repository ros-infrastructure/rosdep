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

def test_InstallerContext_get_os_version_type():
    from rospkg.os_detect import OS_UBUNTU
    from rosdep.installers import InstallerContext, TYPE_CODENAME, TYPE_VERSION
    context = InstallerContext()

    try:
        context.set_os_version_type(OS_UBUNTU, 'bad')
        assert False, "should check type"
    except ValueError:
        pass

    assert TYPE_VERSION == context.get_os_version_type(OS_UBUNTU)
    context.set_os_version_type(OS_UBUNTU, TYPE_CODENAME)
    assert TYPE_CODENAME == context.get_os_version_type(OS_UBUNTU)
    
def test_InstallerContext_os_version_and_name():
    from rosdep.installers import InstallerContext, TYPE_CODENAME, TYPE_VERSION
    context = InstallerContext()
    os_name, os_version = context.get_os_name_and_version()
    assert os_name is not None
    assert os_version is not None
    
    val = ("fakeos", "blah")
    context.set_os_override(*val)
    assert val == context.get_os_name_and_version()

    from mock import Mock
    from rospkg.os_detect import OsDetect
    os_detect_mock = Mock(spec=OsDetect)
    os_detect_mock.get_name.return_value = 'fakeos'
    os_detect_mock.get_version.return_value = 'fakeos-version'
    os_detect_mock.get_codename.return_value = 'fakeos-codename'
    context = InstallerContext(os_detect_mock)
    context.set_os_version_type('fakeos', TYPE_CODENAME)
    os_name, os_version = context.get_os_name_and_version()
    assert os_name == 'fakeos', os_name
    assert os_version == 'fakeos-codename', os_version

    context.set_os_version_type('fakeos', TYPE_VERSION)
    os_name, os_version = context.get_os_name_and_version()
    assert os_name == 'fakeos', os_name
    assert os_version == 'fakeos-version', os_version
    
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
    try:
        context.set_default_os_installer_key(os_key, 'fake-key')
        assert False, "should have raised"
    except KeyError: pass
    try:
        context.get_default_os_installer_key('bad-os')
        assert False, "should have raised"
    except KeyError: pass
    
    installer_key1 = 'fake1'
    installer_key2 = 'fake2'
    class FakeInstaller(Installer):
        pass
    class FakeInstaller2(Installer):
        pass

    # configure our context with two valid installers
    context.set_installer(installer_key1, FakeInstaller)
    context.set_installer(installer_key2, FakeInstaller2)

    # retest set_default_os_installer_key, now with installer_key not configured on os
    try:
        context.set_default_os_installer_key(os_key, installer_key1)
        assert False, "should have raised"
    except KeyError: pass

    # start adding installers for os_key
    context.add_os_installer_key(os_key, installer_key1)
    assert context.get_os_installer_keys(os_key) == [installer_key1]
    context.add_os_installer_key(os_key, installer_key2)
    assert set(context.get_os_installer_keys(os_key)) == set([installer_key1, installer_key2])

    # test default
    assert None == context.get_default_os_installer_key(os_key)
    context.set_default_os_installer_key(os_key, installer_key1)
    assert installer_key1 == context.get_default_os_installer_key(os_key)
    context.set_default_os_installer_key(os_key, installer_key2)    
    assert installer_key2 == context.get_default_os_installer_key(os_key)

    # retest set_default_os_installer_key, now with invalid os
    try:
        context.set_default_os_installer_key('bad-os', installer_key1)
        assert False, "should have raised"
    except KeyError: pass


def test_Installer_tripwire():
    from rosdep.installers import Installer
    try:
        Installer().is_installed(['foo'])
        assert False
    except NotImplementedError: pass
    try:
        Installer().get_install_command(['foo'])
        assert False
    except NotImplementedError: pass
    try:
        Installer().resolve({})
        assert False
    except NotImplementedError: pass
    try:
        Installer().unique([])
        assert False
    except NotImplementedError: pass
    assert Installer().get_depends({}) == []

def detect_fn_empty(packages):
    return []
def detect_fn_all(packages):
    return packages
# return any packages that are string length 1
def detect_fn_single(packages):
    return [p for p in packages if len(p) == 1]


def test_PackageManagerInstaller():
    from rosdep.installers import PackageManagerInstaller
    try:
        PackageManagerInstaller(detect_fn_all).get_install_command(['foo'])
        assert False
    except NotImplementedError: pass

def test_PackageManagerInstaller_resolve():
    from rosdep.installers import PackageManagerInstaller

    installer = PackageManagerInstaller(detect_fn_all)
    assert ['baz'] == installer.resolve(dict(depends=['foo', 'bar'], packages=['baz']))
    assert ['baz', 'bar'] == installer.resolve(dict(packages=['baz', 'bar']))

    #test string logic
    assert ['baz'] == installer.resolve(dict(depends=['foo', 'bar'], packages='baz'))
    assert ['baz', 'bar'] == installer.resolve(dict(packages='baz bar'))

def test_PackageManagerInstaller_depends():
    from rosdep.installers import PackageManagerInstaller

    installer = PackageManagerInstaller(detect_fn_all, supports_depends=True)
    assert ['foo', 'bar'] == installer.get_depends(dict(depends=['foo', 'bar'], packages=['baz']))
    installer = PackageManagerInstaller(detect_fn_all, supports_depends=False)
    assert [] == installer.get_depends(dict(depends=['foo', 'bar'], packages=['baz']))

def test_PackageManagerInstaller_unique():
    from rosdep.installers import PackageManagerInstaller

    installer = PackageManagerInstaller(detect_fn_all)

    assert [] == installer.unique()
    assert [] == installer.unique([])
    assert [] == installer.unique([], [])
    assert ['a'] == installer.unique([], [], ['a'])
    assert ['a'] == installer.unique(['a'], [], ['a'])
    assert set(['a', 'b', 'c']) == set(installer.unique(['a', 'b', 'c'], ['a', 'b', 'c']))
    assert set(['a', 'b', 'c']) == set(installer.unique(['a'], ['b'], ['c']))
    assert set(['a', 'b', 'c']) == set(installer.unique(['a', 'b'], ['c']))    
    assert set(['a', 'b', 'c']) == set(installer.unique(['a', 'b'], ['c', 'a']))    

def test_PackageManagerInstaller_is_installed():
    from rosdep.installers import PackageManagerInstaller

    installer = PackageManagerInstaller(detect_fn_all)
    assert True == installer.is_installed(['a', 'b', 'c']), installer.is_installed(['a', 'b', 'c'])
    installer = PackageManagerInstaller(detect_fn_empty)
    assert False == installer.is_installed(['a', 'b', 'c'])

def test_PackageManagerInstaller_get_packages_to_install():
    from rosdep.installers import PackageManagerInstaller

    installer = PackageManagerInstaller(detect_fn_all)
    assert [] == installer.get_packages_to_install(['a', 'b', 'c'])
    installer = PackageManagerInstaller(detect_fn_empty)
    assert set(['a', 'b', 'c']) == set(installer.get_packages_to_install(['a', 'b', 'c']))
    installer = PackageManagerInstaller(detect_fn_single)
    assert set(['baba', 'cada']) == set(installer.get_packages_to_install(['a', 'baba', 'b', 'cada', 'c']))
    

def test_RosdepInstaller_ctor():
    # tripwire/coverage
    from rosdep import create_default_installer_context
    from rosdep.lookup import RosdepLookup
    from rosdep.installers import RosdepInstaller
    lookup = RosdepLookup.create_from_rospkg()
    context = create_default_installer_context()
    installer = RosdepInstaller(context, lookup)
    assert lookup == installer.lookup
    assert context == installer.installer_context    
