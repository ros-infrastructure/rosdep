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

from rospkg import RosPack, RosStack

def get_test_dir():
    return os.path.abspath(os.path.dirname(__file__))

def get_test_tree_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), 'tree'))

def get_test_rospkgs():
    test_dir = get_test_tree_dir()
    ros_root = os.path.join(test_dir, 'ros')
    ros_package_path = os.path.join(test_dir, 'stacks')
    ros_paths = [ros_root, ros_package_path]
    rospack = RosPack(ros_paths=ros_paths)
    rosstack = RosStack(ros_paths=ros_paths)
    return rospack, rosstack

def test_InstallerContext_ctor():
    from rosdep2.installers import InstallerContext
    from rospkg.os_detect import OsDetect

    context = InstallerContext()
    assert context.get_os_detect() is not None
    assert isinstance(context.get_os_detect(), OsDetect)

    detect = OsDetect()
    context = InstallerContext(detect)
    assert context.get_os_detect() == detect
    assert [] == context.get_installer_keys()
    assert [] == context.get_os_keys()

    context.verbose = True
    assert context.get_os_detect() == detect
    assert [] == context.get_installer_keys()
    assert [] == context.get_os_keys()
    
def test_InstallerContext_get_os_version_type():
    from rospkg.os_detect import OS_UBUNTU
    from rosdep2.installers import InstallerContext, TYPE_CODENAME, TYPE_VERSION
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
    from rosdep2.installers import InstallerContext, TYPE_CODENAME, TYPE_VERSION
    context = InstallerContext()
    context.set_verbose(True)
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
    from rosdep2.installers import InstallerContext, Installer
    from rospkg.os_detect import OsDetect
    detect = OsDetect()
    context = InstallerContext(detect)
    context.verbose = True

    key = 'fake-apt'
    try:
        installer = context.get_installer(key)
        assert False, "should have raised: %s"%(installer)
    except KeyError: pass

    class Foo: pass
    class FakeInstaller(Installer):
        pass
    class FakeInstaller2(Installer):
        pass

    # test TypeError on set_installer
    try:
        context.set_installer(key, 1)
        assert False, "should have raised"
    except TypeError: pass
    try:
        context.set_installer(key, Foo())
        assert False, "should have raised"
    except TypeError: pass
    try:
        # must be instantiated
        context.set_installer(key, FakeInstaller)
        assert False, "should have raised"
    except TypeError: pass

    installer = FakeInstaller()
    installer2 = FakeInstaller2()
    context.set_installer(key, installer)
    assert context.get_installer(key) == installer
    assert context.get_installer_keys() == [key]

    # repeat with same args
    context.set_installer(key, installer)
    assert context.get_installer(key) == installer
    assert context.get_installer_keys() == [key]

    # repeat with new installer
    context.set_installer(key, installer2)
    assert context.get_installer(key) == installer2
    assert context.get_installer_keys() == [key]
    
    # repeat with new key
    key2 = 'fake-port'
    context.set_installer(key2, installer2)
    assert context.get_installer(key2) == installer2
    assert set(context.get_installer_keys()) == set([key, key2])

    # test installer deletion
    key3 = 'fake3'
    context.set_installer(key3, installer2)
    assert context.get_installer(key3) == installer2
    assert set(context.get_installer_keys()) == set([key, key2, key3])
    context.set_installer(key3, None)
    try:
        context.get_installer(key3)
        assert False
    except KeyError:
        pass
    assert set(context.get_installer_keys()) == set([key, key2])

def test_InstallerContext_os_installers():
    from rosdep2.installers import InstallerContext, Installer
    from rospkg.os_detect import OsDetect
    detect = OsDetect()
    context = InstallerContext(detect)
    context.verbose = True

    os_key = 'ubuntu'
    try:
        context.get_os_installer_keys(os_key)
        assert False, "should have raised"
    except KeyError:
        pass
    try:
        context.get_default_os_installer_key(os_key)
        assert False, "should have raised"
    except KeyError:
        pass
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
    context.set_installer(installer_key1, FakeInstaller())
    context.set_installer(installer_key2, FakeInstaller2())

    # start adding installers for os_key
    context.add_os_installer_key(os_key, installer_key1)
    assert context.get_os_installer_keys(os_key) == [installer_key1]

    # retest set_default_os_installer_key, now with installer_key not configured on os
    try:
        context.set_default_os_installer_key(os_key, installer_key2)
        assert False, "should have raised"
    except KeyError as e:
        assert 'add_os_installer' in str(e), e

    # now properly add in key2
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
    from rosdep2.installers import Installer
    try:
        Installer().is_installed('foo')
        assert False
    except NotImplementedError: pass
    try:
        Installer().get_install_command('foo')
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
    from rosdep2.installers import PackageManagerInstaller
    try:
        PackageManagerInstaller(detect_fn_all).get_install_command(['foo'])
        assert False
    except NotImplementedError: pass

def test_PackageManagerInstaller_resolve():
    from rosdep2.model import InvalidData
    from rosdep2.installers import PackageManagerInstaller

    installer = PackageManagerInstaller(detect_fn_all)
    assert ['baz'] == installer.resolve(dict(depends=['foo', 'bar'], packages=['baz']))
    assert ['baz', 'bar'] == installer.resolve(dict(packages=['baz', 'bar']))

    #test string logic
    assert ['baz'] == installer.resolve(dict(depends=['foo', 'bar'], packages='baz'))
    assert ['baz', 'bar'] == installer.resolve(dict(packages='baz bar'))
    assert ['baz'] == installer.resolve('baz')
    assert ['baz', 'bar'] == installer.resolve('baz bar')

    #test list logic
    assert ['baz'] == installer.resolve(['baz'])
    assert ['baz', 'bar'] == installer.resolve(['baz', 'bar'])

    # test invalid data
    try:
        installer.resolve(0)
        assert False, "should have raised"
    except InvalidData: pass

def test_PackageManagerInstaller_depends():
    from rosdep2.installers import PackageManagerInstaller

    installer = PackageManagerInstaller(detect_fn_all, supports_depends=True)
    assert ['foo', 'bar'] == installer.get_depends(dict(depends=['foo', 'bar'], packages=['baz']))
    installer = PackageManagerInstaller(detect_fn_all, supports_depends=False)
    assert [] == installer.get_depends(dict(depends=['foo', 'bar'], packages=['baz']))

def test_PackageManagerInstaller_unique():
    from rosdep2.installers import PackageManagerInstaller

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
    from rosdep2.installers import PackageManagerInstaller

    installer = PackageManagerInstaller(detect_fn_all)
    for r in ['a', 'b', 'c']:
        assert True == installer.is_installed(r), installer.is_installed(r)
    installer = PackageManagerInstaller(detect_fn_empty)
    for r in ['a', 'b', 'c']:
        assert False == installer.is_installed(r), installer.is_installed(r)

def test_PackageManagerInstaller_get_packages_to_install():
    from rosdep2.installers import PackageManagerInstaller

    installer = PackageManagerInstaller(detect_fn_all)
    assert [] == installer.get_packages_to_install([])
    assert [] == installer.get_packages_to_install(['a', 'b', 'c'])
    assert set(['a', 'b', 'c']) == set(installer.get_packages_to_install(['a', 'b', 'c'], reinstall=True))
    
    installer = PackageManagerInstaller(detect_fn_empty)
    assert set(['a', 'b', 'c']) == set(installer.get_packages_to_install(['a', 'b', 'c']))
    assert set(['a', 'b', 'c']) == set(installer.get_packages_to_install(['a', 'b', 'c'], reinstall=True))
    installer = PackageManagerInstaller(detect_fn_single)
    assert set(['baba', 'cada']) == set(installer.get_packages_to_install(['a', 'baba', 'b', 'cada', 'c']))
    
def test_RosdepInstaller_ctor():
    # tripwire/coverage
    from rosdep2 import create_default_installer_context
    from rosdep2.lookup import RosdepLookup
    from rosdep2.installers import RosdepInstaller
    lookup = RosdepLookup.create_from_rospkg()
    context = create_default_installer_context()
    installer = RosdepInstaller(context, lookup)
    assert lookup == installer.lookup
    assert context == installer.installer_context    

def test_RosdepInstaller_get_uninstalled():
    from rosdep2 import create_default_installer_context
    from rosdep2.lookup import RosdepLookup
    from rosdep2.installers import RosdepInstaller
    from rosdep2.platforms.debian import APT_INSTALLER
    
    from rosdep2.lookup import RosdepLookup
    rospack, rosstack = get_test_rospkgs()
    ros_home = os.path.join(get_test_tree_dir(), 'fake')
    
    # create our test fixture.  use most of the default toolchain, but
    # replace the apt installer with one that we can have more fun
    # with.  we will do all tests with ubuntu lucid keys -- other
    # tests should cover different resolution cases.
    lookup = RosdepLookup.create_from_rospkg(rospack=rospack, rosstack=rosstack, ros_home=ros_home)
    context = create_default_installer_context()
    context.set_os_override('ubuntu', 'lucid')
    installer = RosdepInstaller(context, lookup)
    
    # in this first test, detect_fn detects everything as installed
    fake_apt = get_fake_apt(lambda x: x)
    context.set_installer(APT_INSTALLER, fake_apt)

    for verbose in [True, False]:
        tests = [['roscpp_fake'], ['roscpp_fake', 'rospack_fake'], ['empty_package'],
                 ['roscpp_fake', 'rospack_fake', 'empty_package'],
                 ['stack1_p1'],
                 ['stack1_p1', 'stack1_p2'],
                 ['roscpp_fake', 'rospack_fake', 'stack1_p1', 'stack1_p2'],
                 ]
        for test in tests:
            uninstalled, errors = installer.get_uninstalled(test, verbose)
            assert not uninstalled, uninstalled
            assert not errors

    # in this second test, detect_fn detects nothing as installed
    fake_apt = get_fake_apt(lambda x: [])
    context.set_installer(APT_INSTALLER, fake_apt)

    for verbose in [True, False]:
        uninstalled, errors = installer.get_uninstalled(['empty'], verbose)
        assert not uninstalled, uninstalled
        assert not errors

        expected = set(['libltdl-dev', 'libboost1.40-all-dev', 'libtool'])
        uninstalled, errors = installer.get_uninstalled(['roscpp_fake'], verbose)
        assert uninstalled.keys() == [APT_INSTALLER]
        assert set(uninstalled[APT_INSTALLER]) == expected
        assert not errors

        expected = ['libtinyxml-dev']
        uninstalled, errors = installer.get_uninstalled(['rospack_fake'], verbose)
        assert uninstalled.keys() == [APT_INSTALLER]
        assert uninstalled[APT_INSTALLER] == expected, uninstalled
        assert not errors

        expected = set(['dep1-ubuntu', 'p1dep1-ubuntu', 'p1dep2-ubuntu'])
        uninstalled, errors = installer.get_uninstalled(['stack1_p1'], verbose)
        assert uninstalled.keys() == [APT_INSTALLER]
        assert set(uninstalled[APT_INSTALLER]) == expected, uninstalled
        assert not errors

        expected = set(['p1dep1-ubuntu', 'p1dep2-ubuntu','dep1-ubuntu', 'dep2-ubuntu', 'p2dep1-ubuntu'])
        uninstalled, errors = installer.get_uninstalled(['stack1_p2'], verbose)
        assert uninstalled.keys() == [APT_INSTALLER]
        assert set(uninstalled[APT_INSTALLER]) == expected, uninstalled
        assert not errors

        expected = set(['p1dep1-ubuntu', 'p1dep2-ubuntu','dep1-ubuntu', 'dep2-ubuntu', 'p2dep1-ubuntu'])
        uninstalled, errors = installer.get_uninstalled(['stack1_p1', 'stack1_p2'], verbose)
        assert uninstalled.keys() == [APT_INSTALLER]
        assert set(uninstalled[APT_INSTALLER]) == expected, uninstalled
        assert not errors

def get_fake_apt(detect_fn):
    # mainly did this to keep coverage results
    from rosdep2.installers import PackageManagerInstaller
    class FakeAptInstaller(PackageManagerInstaller):
        """ 
        An implementation of the Installer for use on debian style
        systems.
        """
        def __init__(self):
            super(FakeAptInstaller, self).__init__(detect_fn)

        def get_install_command(self, resolved, interactive=True, reinstall=False):
            return [[resolved, interactive, reinstall]]
    return FakeAptInstaller()

def test_RosdepInstaller_get_uninstalled_unconfigured():
    from rosdep2 import create_default_installer_context, RosdepInternalError
    from rosdep2.lookup import RosdepLookup, ResolutionError
    from rosdep2.installers import RosdepInstaller, PackageManagerInstaller
    from rosdep2.platforms.debian import APT_INSTALLER
    
    from rosdep2.lookup import RosdepLookup
    rospack, rosstack = get_test_rospkgs()
    ros_home = os.path.join(get_test_tree_dir(), 'fake')
    
    # create our test fixture.  we want to setup a fixture that cannot resolve the rosdep data in order to test error conditions
    lookup = RosdepLookup.create_from_rospkg(rospack=rospack, rosstack=rosstack, ros_home=ros_home)
    context = create_default_installer_context()
    context.set_os_override('ubuntu', 'lucid')
    installer = RosdepInstaller(context, lookup)
    # - delete the apt installer
    context.set_installer(APT_INSTALLER, None)

    for verbose in [True, False]:
        uninstalled, errors = installer.get_uninstalled(['empty'], verbose)
        assert not uninstalled, uninstalled
        assert not errors

        # make sure there is an error when we lookup something that resolves to an apt depend
        uninstalled, errors = installer.get_uninstalled(['roscpp_fake'], verbose)
        assert not uninstalled, uninstalled
        assert errors.keys() == ['roscpp_fake']

        uninstalled, errors = installer.get_uninstalled(['roscpp_fake', 'stack1_p1'], verbose)
        assert not uninstalled, uninstalled
        assert set(errors.keys()) == set(['roscpp_fake', 'stack1_p1'])
        print(errors)
        assert isinstance(errors['roscpp_fake'], ResolutionError), errors['roscpp_fake'][0]

    # fake/bad installer to test that we re-cast general installer issues
    class BadInstaller(PackageManagerInstaller):
        def __init__(self):
            super(BadInstaller, self).__init__(lambda x: x)
        def get_packages_to_install(*args):
            raise Exception("deadbeef")
    context.set_installer(APT_INSTALLER, BadInstaller())
    try:
        installer.get_uninstalled(['roscpp_fake'])
        assert False, "should have raised"
    except RosdepInternalError as e:
        assert 'apt' in str(e)
    
    # annoying mock to test generally impossible error condition
    from mock import Mock
    lookup = Mock(spec=RosdepLookup)
    lookup.resolve_all.return_value = ({'bad-key': ['stuff']}, [])
    
    installer = RosdepInstaller(context, lookup)
    try:
        installer.get_uninstalled(['roscpp_fake'])
        assert False, "should have raised"
    except RosdepInternalError:
        pass
