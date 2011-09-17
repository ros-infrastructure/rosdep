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

import rospkg

from .loader import RosdepLoader, InvalidRosdepData, ROSDEP_YAML

class RosPkgLoader(RosdepLoader):
    
    def __init__(self, rospack=None, rosstack=None):
        if rospack is None:
            rospack = rospkg.RosPack()
        if rosstack is None:
            rosstack = rospkg.RosStack()

        self._rospack = rospack
        self._rosstack = rosstack
        self._rosdep_yaml_cache = {}
        
    def _load_stack_rosdep_yaml(self, stack_name):
        """
        :returns: parsed YAML data and filename it was loaded from,
          ``(dict, str)``.  Returns ``(None, None)`` if stack does not
          have a rosdep YAML.
        
        :raises: :exc:`InvalidRosdepData`
        :raises: :exc:`rospkg.ResourceNotFound` If stack cannot be located
        """
        stack_dir = self._rosstack.get_path(stack_name)
        filename = os.path.join(stack_dir, ROSDEP_YAML)
        if os.path.isfile(filename):
            with open(filename) as f:
                return self.load_rosdep_yaml(f.read(), filename), filename
        else:
            return None, None
        
    def load_stack(self, stack_name, rosdep_db):
        """
        Load stack data into *rosdep_db*. If the stack has already
        been loaded into *rosdep_db*, this method does nothing.  If
        stack has no rosdep data, it will be initialized with an empty
        data map.

        :raises: :exc:`InvalidRosdepData` if stack rosdep.yaml is invalid
        :raises: :exc:`rospkg.ResourceNotFound` if stack cannot be located

        :returns: ``True`` if stack was loaded.  ``False`` if stack
          was already loaded.
        """
        if rosdep_db.is_loaded(stack_name):
            return
        rosdep_data, filename = self._load_stack_rosdep_yaml(stack_name)
        if rosdep_data is None:
            rosdep_data = {}
        stack_dependencies = self._rosstack.get_depends(stack_name, implicit=False)
        rosdep_db.set_stack_data(stack_name, rosdep_data, stack_dependencies, filename)

    def load_package(self, package_name, rosdep_db):
        """
        Load data for stack that contains package into *rosdep_db*. If
        the package or containing stack has already been loaded into
        *rosdep_db*, this method does nothing.  If package has no
        associated rosdep data, it will be initialized with an empty
        data map.

        :raises: :exc:`InvalidRosdepData` if stack rosdep.yaml is invalid
        :raises: :exc:`rospkg.ResourceNotFound` if stack cannot be located

        :returns: ``True`` if package was loaded, ``False`` if package
          was already loaded or is not part of stack.
        """

        stack_name = self._rospack.stack_of(package_name)
        if stack_name:
            return self.load_stack(stack_name, rosdep_db)

    def get_package_manifest(self, package_name):
        return self._rospack.get_manifest(package_name)

    def get_loadable_packages(self):
        return self._rospack.list()

    def get_loadable_stacks(self):
        return self._rosstack.list()

    def get_package_depends(self, package_name, implicit=True):
        return self._rospack.get_depends(package_name, implicit=implicit)

    def stack_of(self, package_name):
        return self._rospack.stack_of(package_name)
