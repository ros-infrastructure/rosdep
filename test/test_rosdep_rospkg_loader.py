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
import yaml

from mock import Mock
from rospkg import RosPack, RosStack

def get_test_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), 'tree'))
    
def get_rospkg():
    # configure inside of the test tree
    test_dir = get_test_dir()
    ros_root = os.path.join(test_dir, 'ros')
    ros_package_path = os.path.join(test_dir, 'stacks')
    ros_paths = [ros_root, ros_package_path]
    rospack = RosPack(ros_paths=ros_paths)
    rosstack = RosStack(ros_paths=ros_paths)
    return rospack, rosstack

def test_RosPkgLoader():
    from rosdep2.model import RosdepDatabase
    from rosdep2.rospkg_loader import RosPkgLoader
    from rosdep2.loader import InvalidRosdepData
    
    # tripwire
    loader = RosPkgLoader()
    assert loader._rospack is not None
    assert loader._rosstack is not None

    # configure inside of the test tree
    rospack, rosstack = get_rospkg()
    ros_root = rosstack.get_path('ros')
    loader = RosPkgLoader(rospack, rosstack)
    assert loader._rospack == rospack
    assert loader._rosstack == rosstack    

    # test with mock db
    rosdep_db = Mock(spec=RosdepDatabase)
    rosdep_db.is_loaded.return_value = False

    # test with no rosdep.yaml stack
    loader.load_view('empty', rosdep_db)
    rosdep_db.is_loaded.assert_called_with('empty')
    rosdep_db.set_view_data.assert_called_with('empty', {}, ['ros'], None)

    # test invalid stack
    try:
        loader.load_view('invalid', rosdep_db)
        assert False, "should have raised"
    except InvalidRosdepData as e:
        pass

    # test with complicated ros stack.  
    path = os.path.join(ros_root, 'rosdep.yaml')
    with open(path) as f:
        ros_stack_data = yaml.load(f.read())
    loader.load_view('ros', rosdep_db)
    rosdep_db.is_loaded.assert_called_with('ros')
    rosdep_db.set_view_data.assert_called_with('ros', ros_stack_data, [], path)

    # test call on db that is already loaded
    rosdep_db.reset_mock()
    rosdep_db.is_loaded.return_value = True
    path = os.path.join(ros_root, 'rosdep.yaml')
    with open(path) as f:
        ros_stack_data = yaml.load(f.read())
    loader.load_view('ros', rosdep_db)
    rosdep_db.is_loaded.assert_called_with('ros')
    assert rosdep_db.set_view_data.call_args_list == []

    # test get_view_key
    from rospkg import ResourceNotFound
    assert loader.get_view_key('stack1_p1') == 'stack1'
    assert loader.get_view_key('stackless') == None
    try:
        loader.get_view_key('fake')
        assert False, "should error"
    except ResourceNotFound: pass
        
def test_RosPkgLoader_get_loadable():
    from rosdep2.rospkg_loader import RosPkgLoader
    
    rospack, rosstack = get_rospkg()
    loader = RosPkgLoader(rospack, rosstack)
    assert loader._rospack == rospack
    assert loader._rosstack == rosstack    

    keys = loader.get_loadable_resources()
    for p in ['stack1_p1', 'stack1_p2', 'stack1_p3']:
        assert p in keys
    keys = loader.get_loadable_views()        
    for s in ['ros', 'empty', 'invalid', 'stack1']:
        assert s in keys


