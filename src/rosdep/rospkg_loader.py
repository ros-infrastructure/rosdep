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

import rospkg
import yaml

from .loader import RosdepLoader, InvalidRosdepData

ROSDEP_YAML = 'rosdep.yaml'

yaml.add_constructor(
    u'tag:yaml.org,2002:float',
    yaml.constructor.Constructor.construct_yaml_str)

class RosPkgLoader(RosdepLoader):
    
    def __init__(self, rospack=None, rosstack=None):
        if rospack is None:
            rospack = rospkg.RosPack()
        if rosstack is None:
            rosstack = rospkg.RosStack()

        self._rospack = rospack
        self._rosstack = rosstack
        self._rosdep_yaml_cache = {}
        
    def _load_rosdep_yaml(self, stack_name):
        """
        @raise yaml.YAMLError
        @raise rospkg.ResourceNotFound
        """
        stack_dir = self._rosstack.get_path(stack_name)
        filename = os.path.join(stack_dir, ROSDEP_YAML)
        if os.path.isfile(filename):
            with open(filename) as f:
                return yaml.load(f.read())
        
    def load_stack(self, stack_name, rosdep_db):
        """
        Load stack data into rosdep_db. If the stack has already been
        loaded into rosdep_db, this method does nothing.  If stack has
        no rosdep data, it will be initialized with an empty data map.

        @raise InvalidRosdepData
        @raise rospkg.ResourceNotFound
        """
        if rosdep_db.is_loaded(stack_name):
            return
        try:
            rosdep_data = self._load_rosdep_yaml(stack_name) or {}
        except yaml.YAMLError as e:
            raise InvalidRosdepData("Invalid YAML for stack [%s]: %s"%(e, stack_name))
        stack_dependencies = self._rosstack.get_direct_depends(stack_name)
        rosdep_db.set_stack_data(stack_name, rosdep_data, stack_dependencies)

    def load_package(self, package_name, rosdep_db):
        stack_name = self._rospack.stack_of(package_name)
        if stack_name:
            self.load_stack(stack_name, rosdeb_db)

    def load_package_manifest(self, package_name):
        return self._rospack.get_manifest(package_name)

    def get_loadable_packages(self):
        return self._rospack.list()

    def get_loadable_stacks(self):
        return self._rosstack.list()

