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

import catkin_pkg.package
import rospkg
import traceback

from .loader import RosdepLoader
from distutils.version import StrictVersion

# Default view key is the view that packages that are not in stacks
# see. It is the root of all dependencies.  It is superceded by an
# explicit underlay_key.
DEFAULT_VIEW_KEY='*default*'

# Implementation details: this API was originally conceived under the
# rosdep 1 design.  It has since been retrofitted for the rosdep 2
# design, which means it is a bit overbuilt.  There really is no need
# for a notion of views for rospkg -- all rospkgs have the same view.
# It we be nice to refactor this API into something much, much
# simpler, which would probably involve merging RosPkgLoader and
# SourcesListLoader.  RosPkgLoader would provide identification of
# resources and SourcesListLoader would build a *single* view that was
# no longer resource-dependent.
class VersionChecker():
    def __init__(self, version_tags=("version_eq", "version_gt", "version_gte", "version_lt", "version_lte")):
        self.version_tags = version_tags

    def dependency_version_check(self, deps):
        self.dep_version_uniqueness_check(deps)
        self.dep_version_faulty_redundancy(deps)

    def is_version_matching(self, tag1, tag2, version_dep1_str, version_dep2_str):
        version_dep1 = StrictVersion(version_dep1_str)
        version_dep2 = StrictVersion(version_dep2_str)
        if (tag1 == tag2):
            if (tag2 == "version_eq"):
                return (version_dep1 == version_dep2)
            else:
                return True

        if (tag1 == "version_gt" or tag1 == "version_gte"):
            if (tag2 == "version_lte" or tag2 == "version_lt"):
                return False
            if (tag2 == "version_eq"):
                return (version_dep1 < version_dep2)
            return True

        if (tag1 == "version_lt" or tag1 == "version_lte"):
            if (tag2 == "version_gte" or tag2 == "version_gt"):
                return False
            if (tag2 == "version_eq"):
                return (version_dep1 > version_dep2)



    def is_version_consistent(self, dep1, dep2):
        dep1_valid_tags = []
        dep2_valid_tags = []
        for tag in self.version_tags:
            if (getattr(dep1, tag) != None):
                dep1_valid_tags.append(tag)
            if (getattr(dep1,tag) != None):
                dep2_valid_tags.append(tag)

        if (len(dep1_valid_tags) > 0 and len(dep2_valid_tags) > 0):
            for tag_dep_1 in dep1_valid_tags:
                version_dep1_str = getattr(dep1, tag_dep_1)
                for tag_dep_2 in dep2_valid_tags:
                    version_dep2_str = getattr(dep2, tag_dep_2)
                    if (self.is_version_matching(tag_dep_1, tag_dep_2, version_dep1_str, version_dep2_str) == False):
                        return (tag_dep_1, version_dep1_str, tag_dep_2, version_dep2_str), False
        return True

    def ignore_version(self, dep, dep_name=None):
        to_process = []
        if dep_name:
            for i in range(0,len(dep)):
                if (getattr(dep[i], "name") == dep_name):
                    to_process.append(dep[i])
        else:
            to_process.append(dep)

        for i in range(0,len(to_process)):
            for tag in self.version_tags:
                setattr(dep, tag, None)





    def dep_version_uniqueness_check(self, deps):
        """
        This method
        :param deps: list of all dependencies
        """
        for i in range(0, len(deps)):
            version_values = []
            version_tag_provided = 0
            for tag in self.version_tags:
                version_values.append(getattr(deps[i], tag))

            for version_tag in version_values:
                if version_tag != None:
                    version_tag_provided += 1

            if version_tag_provided > 1:
                dep_name = getattr(deps[i], "name")
                error_str = "ERROR: Dependency %s is provided with %d version requirement"%(dep_name, version_tag_provided)
                print(error_str)
                self.ignore_version(deps[i])
                error_str = "ERROR: Versions for %s will be ignored"%(dep_name)
                print (error_str)


    def dep_version_faulty_redundancy(self, deps):
        for actual_dep_index in range(0, len(deps)):
            actual_dep_name = getattr(deps[actual_dep_index], "name")
            for after_actual_dep_index in range(actual_dep_index + 1, len(deps)):
                if actual_dep_name == getattr(deps[after_actual_dep_index], "name"):
                    inconsistent_tags, is_consitent = self.is_version_consistent(deps[actual_dep_index],
                                                                                 deps[after_actual_dep_index])
                    if (is_consitent == False):
                        print("ERROR: A depedencie:[%s] has non consistant version values eg:"%actual_dep_name)
                        print("One XML tag found with %s = %s and the other XML tag found with %s = %s"
                          %(inconsistent_tags[0], inconsistent_tags[1], inconsistent_tags[2], inconsistent_tags[3]))
                        return

class RosPkgLoader(RosdepLoader):
    
    def __init__(self, rospack=None, rosstack=None, underlay_key=None):
        """
        :param underlay_key: If set, all views loaded by this loader
            will depend on this key.
        """
        if rospack is None:
            rospack = rospkg.RosPack()
        if rosstack is None:
            rosstack = rospkg.RosStack()

        self._rospack = rospack
        self._rosstack = rosstack
        self._rosdep_yaml_cache = {}
        self._underlay_key = underlay_key
        self._version_checker = VersionChecker()
        
        # cache computed list of loadable resources
        self._loadable_resource_cache = None
        
    def load_view(self, view_name, rosdep_db, verbose=False):
        """
        Load view data into *rosdep_db*. If the view has already
        been loaded into *rosdep_db*, this method does nothing.  If
        view has no rosdep data, it will be initialized with an empty
        data map.

        :raises: :exc:`InvalidData` if view rosdep.yaml is invalid
        :raises: :exc:`rospkg.ResourceNotFound` if view cannot be located

        :returns: ``True`` if view was loaded.  ``False`` if view
          was already loaded.
        """
        if rosdep_db.is_loaded(view_name):
            return
        if not view_name in self.get_loadable_views():
            raise rospkg.ResourceNotFound(view_name)
        elif view_name == 'invalid':
            raise rospkg.ResourceNotFound("FOUND"+ view_name+str(self.get_loadable_views()))
        if verbose:
            print("loading view [%s] with rospkg loader"%(view_name))
        # chain into underlay if set
        if self._underlay_key:
            view_dependencies = [self._underlay_key]
        else:
            view_dependencies = []
        # no rospkg view has actual data
        rosdep_db.set_view_data(view_name, {}, view_dependencies, '<nodata>')

    def get_loadable_views(self):
        """
        'Views' map to ROS stack names.
        """
        return list(self._rosstack.list()) + [DEFAULT_VIEW_KEY]

    def get_loadable_resources(self):
        """
        'Resources' map to ROS packages names.
        """
        if not self._loadable_resource_cache:
            self._loadable_resource_cache = list(self._rospack.list())
        return self._loadable_resource_cache

    def dep_version_check(self, deps):
        names_with_version = []
        for i in range(0, len(deps) - 1):
            version_values = []
            try:
                version_values.append(getattr(deps[i], "version_eq"))
                version_values.append(getattr(deps[i], "version_gt"))
                version_values.append(getattr(deps[i], "version_gte"))
                version_values.append(getattr(deps[i], "version_lt"))
                version_values.append(getattr(deps[i], "version_lte"))
            except:
                print("ERROR: Dependencies version checking has failed,")
                print("if no version tag has been provided this message can be ignored.")
                return

            for value in version_values:
                if (value != None):
                    names_with_version.append(getattr(deps[i], "name"))
                    break

        if len(names_with_version) > 0:
           names_with_version = set(names_with_version)
           print ("WARNING: The following dependencies have a version specified:")
           for name in names_with_version:
                print(name)
           print ("The version tag(s) provided have been ignored by rosdep.")

    def get_rosdeps(self, resource_name, implicit=True, with_version=False):
        """
        If *resource_name* is a stack, returns an empty list.
        
        :raises: :exc:`rospkg.ResourceNotFound` if *resource_name* cannot be found.
        """
        if resource_name in self.get_loadable_resources():
            m = self._rospack.get_manifest(resource_name)
            if m.is_catkin:
                path = self._rospack.get_path(resource_name)
                pkg = catkin_pkg.package.parse_package(path)
                deps = pkg.build_depends + pkg.buildtool_depends + pkg.run_depends + pkg.test_depends
                self._version_checker.dependency_version_check(deps)
                #self.dep_version_check(deps)
                #self.dep_version_integrity_check(deps)
                name_list = [d.name for d in deps]
                if with_version:
                    return name_list, deps
                else:
                    return name_list, None
            else:
                return self._rospack.get_rosdeps(resource_name, implicit=implicit) , None
        elif resource_name in self._rosstack.list():
            # stacks currently do not have rosdeps of their own, implicit or otherwise
            return [], None
        else:
            raise rospkg.ResourceNotFound(resource_name)

    def get_view_key(self, resource_name):
        """
        Map *resource_name* to a view key.  In rospkg, this maps the
        DEFAULT_VIEW_KEY if *resource_name* exists.

        :raises: :exc:`rospkg.ResourceNotFound`
        """
        if resource_name in self.get_loadable_resources():
            return DEFAULT_VIEW_KEY
        else:
            raise rospkg.ResourceNotFound(resource_name)
