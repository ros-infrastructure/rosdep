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
import yaml

from rospkg import RosPack, RosStack, ResourceNotFound

BASE_URL = 'https://github.com/ros/rosdistro/raw/master/rosdep/base.yaml'
PYTHON_URL = 'https://github.com/ros/rosdistro/raw/master/rosdep/python.yaml'

def get_test_dir():
    return os.path.abspath(os.path.dirname(__file__))

def get_test_tree_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), 'tree'))

def get_cache_dir():
    p = os.path.join(get_test_dir(), 'sources_cache')
    assert os.path.isdir(p)
    return p

def create_test_SourcesListLoader():
    from rosdep2.sources_list import SourcesListLoader
    return SourcesListLoader.create_default(sources_cache_dir=get_cache_dir(), verbose=True)
    
def get_cache_raw():
    cache_rosdep_path = os.path.join(get_cache_dir(), '0a12d6e7b0d47be9b76e7726720e4cb79528cbaa')
    with open(cache_rosdep_path) as f:
        cache_raw = yaml.load(f.read())
    return cache_raw

def get_cache_raw_python():
    cache_rosdep_path = os.path.join(get_cache_dir(), 'f6f4ef95664e373cd4754501337fa217f5b55d91')
    with open(cache_rosdep_path) as f:
        cache_raw = yaml.load(f.read())
    return cache_raw

def get_test_rospkgs():
    test_dir = get_test_tree_dir()
    ros_root = os.path.join(test_dir, 'ros')
    ros_package_path = os.path.join(test_dir, 'stacks')
    ros_paths = [ros_root, ros_package_path]
    rospack = RosPack(ros_paths=ros_paths)
    rosstack = RosStack(ros_paths=ros_paths)
    return rospack, rosstack

FAKE_TINYXML_RULE = """testtinyxml:
  ubuntu:
    lucid:
      apt:
        packages: libtinyxml-dev
  debian: libtinyxml-dev
  osx:
    source:
      uri: 'http://kforge.ros.org/rosrelease/viewvc/sourcedeps/tinyxml/tinyxml-2.6.2-1.rdmanifest'
      md5sum: 13760e61e08c9004493c302a16966c42
  fedora:
    yum:
      packages: tinyxml-devel"""

def test_RosdepDefinition():
    from rosdep2.lookup import RosdepDefinition, ResolutionError, InvalidData
    d = dict(a=1, b=2, c=3)
    def1 = RosdepDefinition('d', d)
    assert def1.rosdep_key == 'd'
    assert def1.data == d
    def2 = RosdepDefinition('d', d, 'file1.txt')
    assert def2.rosdep_key == 'd'
    assert def2.data == d
    assert def2.origin == 'file1.txt'

    # test get_rule_for_platform
    #  - test w/invalid data
    try:
        RosdepDefinition('dbad', 'foo', 'bad.txt').get_rule_for_platform('ubuntu', 'hardy', ['apt'], 'apt')
        assert False, "should have failed"
    except InvalidData: pass
    try:
        RosdepDefinition('dbad', {'ubuntu': 1}, 'bad2.txt').get_rule_for_platform('ubuntu', 'hardy', ['apt'], 'apt')
        assert False, "should have failed"
    except InvalidData: pass
    try:
        RosdepDefinition('dbad', {'ubuntu': {'hardy': 1}}, 'bad2.txt').get_rule_for_platform('ubuntu', 'hardy', ['apt'], 'apt')
        assert False, "should have failed"
    except InvalidData: pass

    #  - test w/valid data
    d2 = yaml.load(FAKE_TINYXML_RULE)['testtinyxml']
    definition = RosdepDefinition('d2', d2, 'file2.txt')
    #  - tripwire
    str(definition)

    val = definition.get_rule_for_platform('fedora', 'fake-version', ['yum', 'source', 'pip'], 'yum')
    assert val == ('yum', dict(packages='tinyxml-devel')), val
    
    val = definition.get_rule_for_platform('debian', 'sid', ['apt', 'source', 'pip'], 'apt')
    assert val == ('apt', 'libtinyxml-dev')

    val = definition.get_rule_for_platform('ubuntu', 'lucid', ['apt', 'source', 'pip'], 'apt')
    assert val == ('apt', dict(packages='libtinyxml-dev')), val

    val = definition.get_rule_for_platform('osx', 'snow', ['macports', 'source', 'pip'], 'macports')
    assert val == ('source', dict(md5sum='13760e61e08c9004493c302a16966c42', uri='http://kforge.ros.org/rosrelease/viewvc/sourcedeps/tinyxml/tinyxml-2.6.2-1.rdmanifest')), val

    # test bad resolutions
    try:
        val = definition.get_rule_for_platform('ubuntu', 'hardy', ['apt', 'source', 'pip'], 'apt')
        assert False, "should have raised: %s"%(str(val))
    except ResolutionError as e:
        assert e.rosdep_key == 'd2'
        assert e.rosdep_data == d2
        assert e.os_name == 'ubuntu'
        assert e.os_version == 'hardy'
        # tripwire
        str(e)

    try:
        val = definition.get_rule_for_platform('fakeos', 'fakeversion', ['apt', 'source', 'pip'], 'apt')
        assert False, "should have raised: %s"%(str(val))
    except ResolutionError as e:
        assert e.rosdep_key == 'd2'
        assert e.rosdep_data == d2
        assert e.os_name == 'fakeos'
        assert e.os_version == 'fakeversion'
        # tripwire
        str(e)

    # test reverse merging OS things (first is default)
    definition = RosdepDefinition('test', {'debian': 'libtest-dev'}, 'fake-1.txt')
    # rule should work as expected before reverse-merge
    val = definition.get_rule_for_platform('debian', 'sid', ['apt', 'source', 'pip'], 'apt')
    assert val == ('apt', 'libtest-dev'), val
    try:
        val = definition.get_rule_for_platform('ubuntu', 'precise', ['apt', 'source', 'pip'], 'apt')
        assert False, "should have failed"
    except ResolutionError as e:
        assert e.rosdep_key == 'test'
        assert e.os_name == 'ubuntu'
        assert e.os_version == 'precise'
        # tripwire?
        str(e)
    definition.reverse_merge({'ubuntu': {'precise': {'apt': 'ros-fuerte-test'}}}, 'fake-gbp.yaml')
    val = definition.get_rule_for_platform('ubuntu', 'precise', ['apt', 'source', 'pip'], 'apt')
    assert val == ('apt', 'ros-fuerte-test'), val
    val = definition.get_rule_for_platform('debian', 'sid', ['apt', 'source', 'pip'], 'apt')
    assert val == ('apt', 'libtest-dev'), val

def test_RosdepView_merge():
    from rosdep2.model import RosdepDatabaseEntry
    from rosdep2.lookup import RosdepView
    
    # rosdep data must be dictionary of dictionaries
    data = dict(a=dict(x=1), b=dict(y=2), c=dict(z=3))
    
    # create empty view and test
    view = RosdepView('common')
    assert len(view.keys()) == 0
    # - tripwire
    str(view)

    # make sure lookups fail if not found
    try:
        view.lookup('notfound')
        assert False, "should have raised KeyError"
    except KeyError as e:
        assert 'notfound' in str(e)
    
    # merge into empty view
    d = RosdepDatabaseEntry(data, [], 'origin')
    view.merge(d)
    assert set(view.keys()) == set(data.keys())
    for k, v in data.items():
        assert view.lookup(k).data == v, "%s vs. %s"%(view.lookup(k), v)
    
    # merge exact same data
    d2 = RosdepDatabaseEntry(data, [], 'origin2')
    view.merge(d2)
    assert set(view.keys()) == set(data.keys())
    for k, v in data.items():
        assert view.lookup(k).data == v

    # merge new for 'd', 'e'
    d3 = RosdepDatabaseEntry(dict(d=dict(o=4), e=dict(p=5)), [], 'origin3')
    view.merge(d3)
    assert set(view.keys()) == set(list(data.keys()) + ['d', 'e'])
    for k, v in data.items():
        assert view.lookup(k).data == v
    assert view.lookup('d').data == dict(o=4)
    assert view.lookup('e').data == dict(p=5)

    # merge different data for 'a'
    d4 = RosdepDatabaseEntry(dict(a=dict(x=2)), [], 'origin4')
    # - first w/o override, should not bump
    view.merge(d4, override=False)
    assert view.lookup('a').data == dict(x=1), view.lookup('a').data
    assert view.lookup('b').data == dict(y=2)
    assert view.lookup('c').data == dict(z=3)
    assert view.lookup('d').data == dict(o=4)
    assert view.lookup('e').data == dict(p=5)
    
    # - now w/ override
    view.merge(d4, override=True)
    assert view.lookup('a').data == dict(x=2)
    assert view.lookup('b').data == dict(y=2)
    assert view.lookup('c').data == dict(z=3)
    assert view.lookup('d').data == dict(o=4)
    assert view.lookup('e').data == dict(p=5)

    # - tripwire
    str(view)

def test_RosdepLookup_get_rosdeps():
    from rosdep2.loader import RosdepLoader
    from rosdep2.lookup import RosdepLookup
    rospack, rosstack = get_test_rospkgs()
    
    sources_loader = create_test_SourcesListLoader()
    lookup = RosdepLookup.create_from_rospkg(rospack=rospack, rosstack=rospack,
                                             sources_loader=sources_loader)
    assert lookup.get_loader() is not None
    assert isinstance(lookup.get_loader(), RosdepLoader)
    print(lookup.get_rosdeps('empty_package'))
    assert lookup.get_rosdeps('empty_package') == []

    try:
        assert lookup.get_rosdeps('not a resource') == []
        assert False, "should have raised"
    except ResourceNotFound:
        pass
    
    print(lookup.get_rosdeps('stack1_p1'))
    assert set(lookup.get_rosdeps('stack1_p1')) == set(['stack1_dep1', 'stack1_p1_dep1', 'stack1_p1_dep2'])
    assert set(lookup.get_rosdeps('stack1_p1', implicit=False)) == set(['stack1_dep1', 'stack1_p1_dep1', 'stack1_p1_dep2'])
    
    print(lookup.get_rosdeps('stack1_p2'))
    assert set(lookup.get_rosdeps('stack1_p2', implicit=False)) == set(['stack1_dep1', 'stack1_dep2', 'stack1_p2_dep1']), set(lookup.get_rosdeps('stack1_p2'))
    assert set(lookup.get_rosdeps('stack1_p2', implicit=True)) == set(['stack1_dep1', 'stack1_dep2', 'stack1_p1_dep1', 'stack1_p1_dep2', 'stack1_p2_dep1']), set(lookup.get_rosdeps('stack1_p2'))    
    
def test_RosdepLookup_get_resources_that_need():
    from rosdep2.lookup import RosdepLookup
    rospack, rosstack = get_test_rospkgs()
    
    sources_loader = create_test_SourcesListLoader()
    lookup = RosdepLookup.create_from_rospkg(rospack=rospack, rosstack=rospack,
                                             sources_loader=sources_loader)

    assert lookup.get_resources_that_need('fake') ==  []
    assert set(lookup.get_resources_that_need('stack1_dep1')) ==  set(['stack1_p1', 'stack1_p2'])
    assert lookup.get_resources_that_need('stack1_dep2') ==  ['stack1_p2']
    assert lookup.get_resources_that_need('stack1_p1_dep1') ==  ['stack1_p1']
    
def test_RosdepLookup_create_from_rospkg():
    from rosdep2.lookup import RosdepLookup
    rospack, rosstack = get_test_rospkgs()

    # these are just tripwire, can't actually test as it depends on external env
    lookup = RosdepLookup.create_from_rospkg()
    
    lookup = RosdepLookup.create_from_rospkg(rospack=rospack)
    assert rospack == lookup.loader._rospack
    
    lookup = RosdepLookup.create_from_rospkg(rospack=rospack, rosstack=rosstack)
    assert rospack == lookup.loader._rospack
    assert rosstack == lookup.loader._rosstack
    
def test_RosdepLookup_get_rosdep_view_for_resource():
    from rosdep2.lookup import RosdepLookup
    from rosdep2.rospkg_loader import DEFAULT_VIEW_KEY, RosPkgLoader
    rospack, rosstack = get_test_rospkgs()
    
    sources_loader = create_test_SourcesListLoader()
    lookup = RosdepLookup.create_from_rospkg(rospack=rospack, rosstack=rosstack,
                                             sources_loader=sources_loader)
    # assumption of our tests
    assert isinstance(lookup.loader, RosPkgLoader)

    # depends on nothing
    cache_raw = get_cache_raw()
    py_cache_raw = get_cache_raw_python()
    # - first pass: no cache
    ros_view = lookup.get_rosdep_view_for_resource('roscpp_fake')
    libtool = ros_view.lookup('testlibtool')
    assert BASE_URL == libtool.origin
    assert cache_raw['testlibtool'] == libtool.data
    python = ros_view.lookup('testpython')
    assert PYTHON_URL == python.origin
    assert py_cache_raw['testpython'] == python.data

    # package not in stack, should return 
    assert lookup.get_rosdep_view_for_resource('just_a_package').name is DEFAULT_VIEW_KEY
    
def test_RosdepLookup_get_rosdep_view():
    from rosdep2.lookup import RosdepLookup
    rospack, rosstack = get_test_rospkgs()
    
    sources_loader = create_test_SourcesListLoader()
    lookup = RosdepLookup.create_from_rospkg(rospack=rospack, rosstack=rosstack,
                                             sources_loader=sources_loader)

    # depends on nothing
    cache_raw = get_cache_raw()
    py_cache_raw = get_cache_raw_python()
    # - first pass: no cache
    ros_view = lookup.get_rosdep_view('ros')
    libtool = ros_view.lookup('testlibtool')
    assert BASE_URL == libtool.origin
    assert cache_raw['testlibtool'] == libtool.data
    python = ros_view.lookup('testpython')
    assert PYTHON_URL == python.origin
    assert py_cache_raw['testpython'] == python.data, python.data

    # - second pass: with cache
    ros_view = lookup.get_rosdep_view('ros')
    libtool = ros_view.lookup('testlibtool')
    assert BASE_URL == libtool.origin
    assert cache_raw['testlibtool'] == libtool.data
    
    # depends on ros
    stack1_view = lookup.get_rosdep_view('stack1')
    stack1_rosdep_path = os.path.join(rosstack.get_path('stack1'), 'rosdep.yaml')
    
    # - make sure ros data is available 
    libtool = stack1_view.lookup('testlibtool')
    assert BASE_URL == libtool.origin
    assert cache_raw['testlibtool'] == libtool.data
    python = stack1_view.lookup('testpython')
    assert PYTHON_URL == python.origin
    assert py_cache_raw['testpython'] == python.data
    
def test_RosdepLookup_get_errors():
    from rosdep2.lookup import RosdepLookup
    rospack, rosstack = get_test_rospkgs()
    tree_dir = get_test_tree_dir()
    sources_loader = create_test_SourcesListLoader()
    lookup = RosdepLookup.create_from_rospkg(rospack=rospack, rosstack=rosstack,
                                             sources_loader=sources_loader)

    # shouldn't be any errors (yet)
    assert lookup.get_errors() == []

    # force errors
    lookup._load_all_views(lookup.loader)
    
    #TODO: force errors.  Previous tests relied on bad stack views.
    #Now we need a bad sources cache.
    
def test_RosdepLookup_get_views_that_define():
    from rosdep2.lookup import RosdepLookup
    rospack, rosstack = get_test_rospkgs()
    tree_dir = get_test_tree_dir()
    sources_loader = create_test_SourcesListLoader()
    lookup = RosdepLookup.create_from_rospkg(rospack=rospack, rosstack=rosstack,
                                             sources_loader=sources_loader)

    val = lookup.get_views_that_define('testboost')
    assert len(val) == 1
    entry = val[0]
    assert entry == (BASE_URL, BASE_URL), entry

    val = lookup.get_views_that_define('testpython')
    assert len(val) == 1
    entry = val[0]
    assert entry == (PYTHON_URL, PYTHON_URL), entry
    
def test_RosdepLookup_resolve_all_errors():
    from rosdep2.installers import InstallerContext
    from rosdep2.lookup import RosdepLookup, ResolutionError
    rospack, rosstack = get_test_rospkgs()
    sources_loader = create_test_SourcesListLoader()
    lookup = RosdepLookup.create_from_rospkg(rospack=rospack, rosstack=rosstack,
                                             sources_loader=sources_loader)
    # the installer context has nothing in it, lookups will fail
    installer_context = InstallerContext()
    installer_context.set_os_override('ubuntu', 'lucid')

    resolutions, errors = lookup.resolve_all(['rospack_fake'], installer_context)
    assert 'rospack_fake' in errors

    resolutions, errors = lookup.resolve_all(['not_a_resource'], installer_context)
    assert 'not_a_resource' in errors, errors

def test_RosdepLookup_resolve_errors():
    from rosdep2.installers import InstallerContext
    from rosdep2.lookup import RosdepLookup, ResolutionError
    rospack, rosstack = get_test_rospkgs()
    
    sources_loader = create_test_SourcesListLoader()
    lookup = RosdepLookup.create_from_rospkg(rospack=rospack, rosstack=rosstack,
                                             sources_loader=sources_loader)
    # the installer context has nothing in it, lookups will fail
    installer_context = InstallerContext()
    installer_context.set_os_override('ubuntu', 'lucid')

    try:
        lookup.resolve('testtinyxml', 'rospack_fake', installer_context)
        assert False, "should have raised"
    except ResolutionError as e:
        assert "Unsupported OS" in str(e), str(e)

    try:
        lookup.resolve('fakedep', 'rospack_fake', installer_context)
        assert False, "should have raised"
    except ResolutionError as e:
        assert "Cannot locate rosdep definition" in str(e), str(e)

def test_RosdepLookup_resolve():
    from rosdep2 import create_default_installer_context
    from rosdep2.lookup import RosdepLookup
    rospack, rosstack = get_test_rospkgs()
    
    sources_loader = create_test_SourcesListLoader()
    lookup = RosdepLookup.create_from_rospkg(rospack=rospack, rosstack=rosstack,
                                             sources_loader=sources_loader)
    installer_context = create_default_installer_context()
    installer_context.set_os_override('ubuntu', 'lucid')

    # repeat for caching
    for count in range(0, 2):
        installer_key, resolution, dependencies = lookup.resolve('testtinyxml', 'rospack_fake', installer_context)
        assert 'apt' == installer_key
        assert ['libtinyxml-dev'] == resolution
        assert [] == dependencies

        installer_key, resolution, dependencies = lookup.resolve('testboost', 'roscpp_fake', installer_context)
        assert 'apt' == installer_key
        assert ['libboost1.40-all-dev'] == resolution
        assert [] == dependencies

        installer_key, resolution, dependencies = lookup.resolve('testlibtool', 'roscpp_fake', installer_context)
        assert 'apt' == installer_key
        assert set(['libtool', 'libltdl-dev']) == set(resolution)
        assert [] == dependencies


def test_RosdepLookup_resolve_all():
    from rosdep2 import create_default_installer_context
    from rosdep2.lookup import RosdepLookup
    rospack, rosstack = get_test_rospkgs()
    
    sources_loader = create_test_SourcesListLoader()
    lookup = RosdepLookup.create_from_rospkg(rospack=rospack, rosstack=rosstack,
                                             sources_loader=sources_loader)
    installer_context = create_default_installer_context()
    installer_context.set_os_override('ubuntu', 'lucid')

    # repeat for caching
    lookup.verbose = True
    for count in range(0, 2):
        resolutions, errors = lookup.resolve_all(['rospack_fake', 'roscpp_fake'], installer_context)
        assert not errors, errors
        installer_keys, resolveds = zip(*resolutions)
        assert 'apt' in installer_keys
        apt_resolutions = []
        for k, v in resolutions:
            if k == 'apt':
                apt_resolutions.extend(v)
        assert set(apt_resolutions) == set(['libtinyxml-dev', 'libboost1.40-all-dev', 'libtool', 'libltdl-dev']), set(apt_resolutions)
        
