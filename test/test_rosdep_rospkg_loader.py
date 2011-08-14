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

"""
Library for loading rosdep files from the ROS package/stack
filesystem.
"""

import os
import yaml

from mock import Mock
from rospkg import RosPack, RosStack

def get_test_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), 'tree'))
    
def test_RosPkgLoader():
    from rosdep.model import RosdepDatabase
    from rosdep.rospkg_loader import RosPkgLoader
    
    test_dir = get_test_dir()
    ros_root = os.path.join(test_dir, 'ros')
    ros_package_path = os.path.join(test_dir, 'stacks')
    rospack = RosPack(ros_root, ros_package_path)
    rosstack = RosStack(ros_root, ros_package_path)
    loader = RosPkgLoader(rospack, rosstack)
    assert loader._rospack == rospack
    assert loader._rosstack == rosstack    

    rosdep_db = Mock(spec=RosdepDatabase)
    rosdep_db.is_loaded.return_value = False

    # test with no rosdep.yaml stack
    loader.load_stack('empty', rosdep_db)
    rosdep_db.is_loaded.assert_called_with('empty')
    rosdep_db.set_stack_data.assert_called_with('empty', {}, ['ros'])

    # test with complicated ros stack
    with open(os.path.join(ros_root, 'rosdep.yaml')) as f:
        ros_stack_data = yaml.load(f.read())
    loader.load_stack('ros', rosdep_db)
    rosdep_db.is_loaded.assert_called_with('ros')
    rosdep_db.set_stack_data.assert_called_with('ros', ros_stack_data, [])

    #TODO
    if 0:
        rosdep_db.reset_mock()
        loader.load_package(package_name, rosdep_db)
        assert False

    packages = loader.get_loadable_packages()
    for p in ['stack1_p1', 'stack1_p2', 'stack1_p3']:
        assert p in packages
    stacks = loader.get_loadable_stacks()
    for s in ['ros', 'empty', 'invalid', 'stack1']:
        assert s in stacks, stacks

    # TODO: test package not part of stack
    if 0:
        loader.load_package_manifest(package_name)
    # TODO: test invalid stack
    from rosdep.loader import InvalidRosdepData
    try:
        loader.load_stack('invalid', rosdep_db)
        assert False, "should have raised"
    except InvalidRosdepData as e:
        pass

