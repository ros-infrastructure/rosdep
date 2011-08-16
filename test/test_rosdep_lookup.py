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
import yaml

from rospkg import RosPack, RosStack

def get_test_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), 'tree'))

def get_test_rospkgs():
    test_dir = get_test_dir()
    ros_root = os.path.join(test_dir, 'ros')
    ros_package_path = os.path.join(test_dir, 'stacks')
    rospack = RosPack(ros_root, ros_package_path)
    rosstack = RosStack(ros_root, ros_package_path)
    return rospack, rosstack

def test_RosdepDefinition():
    from rosdep.lookup import RosdepDefinition
    d = dict(a=1, b=2, c=3)
    def1 = RosdepDefinition(d)
    assert def1.data == d
    def2 = RosdepDefinition(d, 'file1.txt')
    assert def2.data == d
    assert def2.origin == 'file1.txt'
    
def test_RosdepConflict():
    from rosdep.lookup import RosdepConflict, RosdepDefinition
    def1 = RosdepDefinition(dict(a=1), 'origin1')
    def2 = RosdepDefinition(dict(b=2), 'origin2')
    
    ex = RosdepConflict('foo', def1, def2)
    str_ex = str(ex)
    print(str_ex)
    assert def1.origin in str_ex
    assert def2.origin in str_ex
    
def test_RosdepView_merge():
    from rosdep.model import RosdepDatabaseEntry
    from rosdep.lookup import RosdepView, RosdepConflict
    
    data = dict(a=1, b=2, c=3)
    
    # create empty view and test
    view = RosdepView('common')
    assert view.keys() == []

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
    d3 = RosdepDatabaseEntry(dict(d=4, e=5), [], 'origin3')
    view.merge(d3)
    assert set(view.keys()) == set(data.keys() + ['d', 'e'])
    for k, v in data.items():
        assert view.lookup(k).data == v
    assert view.lookup('d').data == 4
    assert view.lookup('e').data == 5

    # merge different data for 'a'
    d4 = RosdepDatabaseEntry(dict(a=2), [], 'origin4')
    # - first w/o override, should raise conflict
    try:
        view.merge(d4, override=False)
        assert False, "should have raised RosdepConflict"
    except RosdepConflict as ex:
        assert ex.definition1.origin == 'origin'
        assert ex.definition2.origin == 'origin4' 
    
    # - now w/ override
    view.merge(d4, override=True)
    assert view.lookup('a').data == 2
    assert view.lookup('b').data == 2
    assert view.lookup('c').data == 3
    assert view.lookup('d').data == 4
    assert view.lookup('e').data == 5


def test_RosdepLookup():
    from rosdep.lookup import RosdepLookup

def test_RosdepLookup_get_rosdeps():
    from rosdep.lookup import RosdepLookup
    rospack, rosstack = get_test_rospkgs()
    ros_home = os.path.join(get_test_dir(), 'fake')
    
    lookup = RosdepLookup.create_from_rospkg(rospack=rospack, rosstack=rospack, ros_home=ros_home)
    print(lookup.get_rosdeps('empty_package'))
    assert lookup.get_rosdeps('empty_package') == []

    print(lookup.get_rosdeps('stack1_p1'))
    assert set(lookup.get_rosdeps('stack1_p1')) == set(['stack1_dep1', 'stack1_p1_dep1', 'stack1_p1_dep2'])

    print(lookup.get_rosdeps('stack1_p2'))
    assert set(lookup.get_rosdeps('stack1_p2')) == set(['stack1_dep1', 'stack1_dep2', 'stack1_p2_dep1'])
    
def test_RosdepLookup_get_rosdeps():
    from rosdep.lookup import RosdepLookup
    rospack, rosstack = get_test_rospkgs()
    ros_home = os.path.join(get_test_dir(), 'fake')
    
    lookup = RosdepLookup.create_from_rospkg(rospack=rospack, rosstack=rospack, ros_home=ros_home)
    print(lookup.get_rosdeps('empty_package'))
    assert lookup.get_rosdeps('empty_package') == []

    print(lookup.get_rosdeps('stack1_p1'))
    assert set(lookup.get_rosdeps('stack1_p1')) == set(['stack1_dep1', 'stack1_p1_dep1', 'stack1_p1_dep2'])

    print(lookup.get_rosdeps('stack1_p2'))
    assert set(lookup.get_rosdeps('stack1_p2')) == set(['stack1_dep1', 'stack1_dep2', 'stack1_p2_dep1'])

def test_RosdepLookup_what_needs():
    from rosdep.lookup import RosdepLookup
    rospack, rosstack = get_test_rospkgs()
    ros_home = os.path.join(get_test_dir(), 'fake')
    
    lookup = RosdepLookup.create_from_rospkg(rospack=rospack, rosstack=rospack, ros_home=ros_home)

    assert lookup.what_needs('fake') ==  []
    assert set(lookup.what_needs('stack1_dep1')) ==  set(['stack1_p1', 'stack1_p2'])
    assert lookup.what_needs('stack1_dep2') ==  ['stack1_p2']
    assert lookup.what_needs('stack1_p1_dep1') ==  ['stack1_p1']
    
def test_RosdepLookup_create_from_rospkg():
    from rosdep.lookup import RosdepLookup
    rospack, rosstack = get_test_rospkgs()
    ros_home = os.path.join(get_test_dir(), 'fake')

    # these are just tripwire, can't actually test as it depends on external env
    lookup = RosdepLookup.create_from_rospkg()
    
    lookup = RosdepLookup.create_from_rospkg(rospack=rospack)
    assert rospack == lookup.loader._rospack
    
    lookup = RosdepLookup.create_from_rospkg(rospack=rospack, rosstack=rosstack)
    assert rospack == lookup.loader._rospack
    assert rosstack == lookup.loader._rosstack
    
    lookup = RosdepLookup.create_from_rospkg(ros_home=ros_home)
    
    lookup = RosdepLookup.create_from_rospkg(os_name='foo')
    assert 'foo' == lookup.default_os_name
    
    lookup = RosdepLookup.create_from_rospkg(os_version='foo-version')
    assert 'foo-version' == lookup.default_os_version
    
def test_RosdepLookup_get_rosdep_view():
    from rosdep.lookup import RosdepLookup
    rospack, rosstack = get_test_rospkgs()
    ros_home = os.path.join(get_test_dir(), 'fake')
    
    lookup = RosdepLookup.create_from_rospkg(rospack=rospack, rosstack=rosstack, ros_home=ros_home)

    # depends on nothing
    ros_view = lookup.get_rosdep_view('ros')
    ros_rosdep_path = os.path.join(rosstack.get_path('ros'), 'rosdep.yaml')
    with open(ros_rosdep_path) as f:
        ros_raw = yaml.load(f.read())
    libtool = ros_view.lookup('libtool')
    assert ros_rosdep_path == libtool.origin
    assert ros_raw['libtool'] == libtool.data
    python = ros_view.lookup('python')
    assert ros_rosdep_path == python.origin
    assert ros_raw['python'] == python.data
    
    # depends on ros
    stack1_view = lookup.get_rosdep_view('stack1')
    stack1_rosdep_path = os.path.join(rosstack.get_path('stack1'), 'rosdep.yaml')
    
    # - make sure a couple of deps made it
    s1d1 = stack1_view.lookup('stack1_dep1')
    assert s1d1.origin == stack1_rosdep_path
    assert s1d1.data == dict(ubuntu='dep1-ubuntu', debian='dep1-debian')
    s1p2d1 = stack1_view.lookup('stack1_p2_dep1')
    assert s1p2d1.origin == stack1_rosdep_path
    assert s1p2d1.data == dict(ubuntu='p2dep1-ubuntu', debian='p2dep1-debian'), s1p2d1.data

    # - make sure ros data is available 
    libtool = stack1_view.lookup('libtool')
    assert ros_rosdep_path == libtool.origin
    assert ros_raw['libtool'] == libtool.data
    python = stack1_view.lookup('python')
    assert ros_rosdep_path == python.origin
    assert ros_raw['python'] == python.data
