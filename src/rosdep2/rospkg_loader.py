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

from __future__ import print_function

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
        # cache computed list of loadable resources
        self._loadable_resource_cache = None
        
    def _load_view_rosdep_yaml(self, view_name):
        """
        Load the rosdep.yaml for the view (ROS stack).
        
        :returns: parsed YAML data and filename it was loaded from,
          ``(dict, str)``.  Returns ``(None, None)`` if view does not
          have a rosdep YAML.
        
        :raises: :exc:`InvalidRosdepData`
        :raises: :exc:`rospkg.ResourceNotFound` If view cannot be located
        """
        stack_dir = self._rosstack.get_path(view_name)
        filename = os.path.join(stack_dir, ROSDEP_YAML)
        if os.path.isfile(filename):
            with open(filename) as f:
                return self.load_rosdep_yaml(f.read(), filename), filename
        else:
            return None, None
        
    def load_view(self, view_name, rosdep_db, verbose=False):
        """
        Load view data into *rosdep_db*. If the view has already
        been loaded into *rosdep_db*, this method does nothing.  If
        view has no rosdep data, it will be initialized with an empty
        data map.

        :raises: :exc:`InvalidRosdepData` if view rosdep.yaml is invalid
        :raises: :exc:`rospkg.ResourceNotFound` if view cannot be located

        :returns: ``True`` if view was loaded.  ``False`` if view
          was already loaded.
        """
        if rosdep_db.is_loaded(view_name):
            return
        if verbose:
            print("loading view [%s] with rospkg loader"%(view_name))
        rosdep_data, filename = self._load_view_rosdep_yaml(view_name)
        if rosdep_data is None:
            if verbose:
                print("view [%s] has no rosdep data"%(view_name))
            rosdep_data = {}
        view_dependencies = self._rosstack.get_depends(view_name, implicit=False)
        if verbose:
            print("view [%s]: dependencies are [%s]"%(view_name, ', '.join(view_dependencies)))
        rosdep_db.set_view_data(view_name, rosdep_data, view_dependencies, filename)

    def get_loadable_views(self):
        """
        'Views' map to ROS stack names.
        """
        return self._rosstack.list()

    def get_loadable_resources(self):
        """
        'Resources' map to ROS packages names.
        """
        # loading of catkinized ROS packages is currently excluded as
        # they do not have a stack in the install layout.
        if not self._loadable_resource_cache:
            loadable_list = self._rospack.list()
            self._loadable_resource_cache = \
                                          [x for x in loadable_list if not self._rospack.get_manifest(x).is_catkin]
        return self._loadable_resource_cache

    def get_rosdeps(self, resource_name, implicit=True):
        """
        If *resource_name* is a stack, returns an empty list.
        
        :raises: :exc:`rospkg.ResourceNotFound` if *resource_name* cannot be found.
        """
        if resource_name in self._rospack.list():
            return self._rospack.get_rosdeps(resource_name, implicit=implicit)
        elif resource_name in self._rosstack.list():
            # stacks currently do not have rosdeps of their own, implicit or otherwise
            return []
        else:
            raise rospkg.ResourceNotFound(resource_name)

    def get_view_key(self, resource_name):
        """
        Map *resource_name* to a view key.  In rospkg, this maps a ROS
        package name to a ROS stack name.  If *resource_name* is a ROS
        stack name, it returns the ROS stack name.

        :raises: :exc:`rospkg.ResourceNotFound`
        """
        if resource_name in self._rospack.list():
            # assume it's a package, and get the stack
            return self._rospack.stack_of(resource_name)
        elif resource_name in self._rosstack.list():
            return resource_name
        else:
            raise rospkg.ResourceNotFound(resource_name)
