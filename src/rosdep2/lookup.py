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

# Author Tully Foote/tfoote@willowgarage.com, Ken Conley/kwc@willowgarage.com

from __future__ import print_function

import os
import sys
import traceback
import yaml

from collections import defaultdict

from rospkg import RosPack, RosStack, get_ros_home, ResourceNotFound
from rospkg.os_detect import OsDetect

from .core import RosdepInternalError, rd_debug
from .model import RosdepDatabase, RosdepDatabaseEntry, InvalidRosdepData
from .rospkg_loader import RosPkgLoader

# key for representing .ros/rosdep.yaml override entry
OVERRIDE_ENTRY = '.ros'

class RosdepDefinition(object):
    """
    Single rosdep dependency definition.  This data is stored as the
    raw dictionary definition for the dependency.

    See REP 111, 'Multiple Package Manager Support for Rosdep' for a
    discussion of this raw format.
    """
    
    def __init__(self, rosdep_key, data, origin="<dynamic>"):
        """
        :param rosdep_key: key/name of rosdep dependency
        :param data: raw rosdep data for a single rosdep dependency, ``dict``
        :param origin: string that indicates where data originates from (e.g. filename)
        """
        self.rosdep_key = rosdep_key
        self.data = data
        self.origin = origin


    def get_rule_for_platform(self, os_name, os_version, installer_keys, default_installer_key):
        """
        Get installer_key and rule for the specified rule.  See REP 111 for precedence rules.

        :param os_name: OS name to get rule for
        :param os_version: OS version to get rule for
        :param installer_keys: Keys of installers for platform, ``[str]``
        :param default_installer_key: Default installer key for platform, ``[str]``
        :returns: (installer_key, rosdep_args_dict), ``(str, dict)``

        :raises: :exc:`ResolutionError` If no rule is available
        :raises: :exc:`InvalidRosdepData` If rule data is not valid
        """
        rosdep_key = self.rosdep_key
        data = self.data

        if type(data) != dict:
            raise InvalidRosdepData("rosdep value for [%s] must be a dictionary"%(self.rosdep_key), origin=self.origin)
        if os_name not in data:
            raise ResolutionError(rosdep_key, data, os_name, os_version, "No definition of [%s] for OS [%s]"%(rosdep_key, os_name))
        data = data[os_name]
        return_key = default_installer_key
        
        # REP 111: "rosdep first interprets the key as a
        # PACKAGE_MANAGER. If this test fails, it will be interpreted
        # as an OS_VERSION."
        if type(data) == dict:
            for installer_key in installer_keys:
                if installer_key in data:
                    data = data[installer_key]
                    return_key = installer_key
                    break
            else:
                # data must be a dictionary, string, or list
                if type(data) == dict:
                    # check for
                    #   hardy:
                    #     apt:
                    #       stuff

                    # we've already checked for PACKAGE_MANAGER_KEY, so
                    # version key must be present here for data to be valid
                    # dictionary value.
                    if os_version not in data:
                        raise ResolutionError(rosdep_key, self.data, os_name, os_version, "No definition for OS version [%s]"%(os_version))
                    data = data[os_version]
                    if type(data) == dict:
                        for installer_key in installer_keys:
                            if installer_key in data:
                                data = data[installer_key]
                                return_key = installer_key                    
                                break

        if type(data) not in (dict, list, type('str')):
            raise InvalidRosdepData("rosdep OS definition for [%s:%s] must be a dictionary, string, or list: %s"%(self.rosdep_key, os_name, data), origin=self.origin)

        return return_key, data

    def __str__(self):
        return "%s:\n%s"%(self.origin, yaml.dump(self.data, default_flow_style=False))
    
class ResolutionError(Exception):

    def __init__(self, rosdep_key, rosdep_data, os_name, os_version, message):
        self.rosdep_key = rosdep_key
        self.rosdep_data = rosdep_data
        self.os_name = os_name
        self.os_version = os_version
        super(ResolutionError, self).__init__(message)

    def __str__(self):
        if self.rosdep_data:
            pretty_data = yaml.dump(self.rosdep_data, default_flow_style=False)
        else:
            pretty_data = '<no data>'
        return """%s
\trosdep key : %s
\tOS name    : %s
\tOS version : %s
\tData: %s"""%(self.args[0], self.rosdep_key, self.os_name, self.os_version, pretty_data)

class RosdepConflict(Exception):
    """
    Rosdep rules do not have compatbile definitions.
    """

    def __init__(self, definition_name, definition1, definition2):
        """
        :apram definition_name: name of rosdep key that has conflicting definition.
        :param definition1: Existing rule, :class:`RosdepDefinition`
        :param definition2: Conflicting rule, :class:`RosdepDefinition`
        """
        self.definition_name = definition_name
        self.definition1 = definition1
        self.definition2 = definition2
        
    def __str__(self):
        pretty_data1 = yaml.dump(self.definition1.data, default_flow_style=False)
        pretty_data2 = yaml.dump(self.definition2.data, default_flow_style=False)
        return """Rules for %s do not match:
In [%s]

%s 

In [%s]

%s"""%(self.definition_name, self.definition1.origin, pretty_data1, self.definition2.origin, pretty_data2)
    
class RosdepView(object):
    """
    View of :class:`RosdepDatabase`.  Unlike :class:`RosdepDatabase`,
    which stores :class:`RosdepDatabaseEntry` data for all stacks, a
    view merges entries for a particular stack.  This view can then be
    queries to lookup and resolve individual rosdep dependencies.
    """
    
    def __init__(self, name):
        self.name = name
        self.rosdep_defs = {} # {str: RosdepDefinition}

    def __str__(self):
        return '\n'.join(["%s: %s"%val for val in self.rosdep_defs.items()])
            
    def lookup(self, rosdep_name):
        """
        :returns: :class:`RosdepDefinition`
        :raises: :exc:`KeyError` If *rosdep_name* is not declared
        """
        return self.rosdep_defs[rosdep_name]

    def keys(self):
        """
        :returns: list of rosdep names in this view
        """
        return self.rosdep_defs.keys()
        
    def merge(self, update_entry, override=False):
        """
        Merge rosdep database update into main database

        :raises: :exc:`RosdepConflict`
        """
        db = self.rosdep_defs

        for dep_name, dep_data in update_entry.rosdep_data.items():
            # convert data into RosdepDefinition model
            update_definition = RosdepDefinition(dep_name, dep_data, update_entry.origin)
            if override or not dep_name in db:
                db[dep_name] = update_definition
            else:
                definition = db[dep_name]
                curr_data = definition.data
                # First, check for conflict.  Conflict's are
                # OS-specific.  We cannot check at a finer granularity
                # as keys further in the hierarchy are opaque.
                for k, v in dep_data.items():
                    if k in curr_data and curr_data[k] != v:
                        raise RosdepConflict(dep_name, definition, update_definition) 
                
                # If no conflict, do an update
                curr_data.update(dep_data)

class RosdepLookup(object):
    """
    Lookup rosdep definitions.  Provides API for most
    non-install-related commands for rosdep.

    :class:`RosdepLookup` caches data as it is loaded, so changes made
    on the filesystem will not be reflected if the rosdep information
    has already been loaded.
    """
    
    def __init__(self, rosdep_db, loader,
                 override_entry=None):
        """
        :param loader: Loader to use for loading rosdep data by stack
          name, ``RosdepLoader``
        :param rosdep_db: Database to load definitions into, :class:`RosdepDatabase`
        :param override_entry: (optional) provide a database entry
          that overrides all other entries, :class:`RosdepDatabaseEntry`
        """
        self.rosdep_db = rosdep_db
        self.loader = loader

        self._view_cache = {} # {str: {RosdepView}}
        self._resolve_cache = {} # {str : (os_name, os_version, installer_key, resolution, dependencies)}
        
        # ROS_HOME/rosdep.yaml can override 
        self.override_entry  = override_entry

        # some APIs that deal with the entire environment save errors
        # in to self.errors instead of raising them in order to be
        # robust to single-stack faults.
        self.errors = []

        # flag for turning on printing to console
        self.verbose = False

    def get_loader(self):
        return self.loader
    
    def get_errors(self):
        """
        Retrieve error state for API calls that do not directly report
        error state.  This is the case for APIs like
        :meth:`RosdepLookup.where_defined` that are meant to be
        fault-tolerant to single-stack failures.

        :returns: List of exceptions, ``[Exception]``
        """
        return self.errors[:]
    
    def get_rosdeps(self, resource_name, implicit=True):
        """
        Get rosdeps that *resource_name* (e.g. package) requires.

        :param implicit: If ``True``, include implicit rosdep
          dependencies. Default: ``True``.

        :returns: list of rosdep names, ``[str]``
        """
        return self.loader.get_rosdeps(resource_name, implicit=implicit)

    def get_resources_that_need(self, rosdep_name):
        """
        :param rosdep_name: name of rosdep dependency
        
        :returns: list of package names that require rosdep, ``[str]``
        """
        return [k for k in self.loader.get_loadable_resources() if rosdep_name in self.get_rosdeps(k, implicit=False)]

    @staticmethod
    def create_from_rospkg(rospack=None, rosstack=None, ros_home=None):
        """
        Create :class:`RosdepLookup` based on current ROS package
        environment.

        :param rospack: (optional) Override :class:`rospkg.RosPack`
          instance used to crawl ROS packages.
        :param rosstack: (optional) Override :class:`rospkg.RosStack`
          instance used to crawl ROS stacks.
        """
        # initialize the loader
        if rospack is None:
            rospack = RosPack()
        if rosstack is None:
            rosstack = RosStack()
        if ros_home is None:
            ros_home = get_ros_home()

        loader = RosPkgLoader(rospack=rospack, rosstack=rosstack)
        rosdep_db = RosdepDatabase()
        
        # Load ros_home/rosdep.yaml, if present.  It will be used to
        # override individual stack views.
        override_entry = None
        path = os.path.join(ros_home, "rosdep.yaml")
        if os.path.exists(path):
            with open(path, 'r') as f:
                data = loader.load_rosdep_yaml(f.read(), path)
            override_entry = RosdepDatabaseEntry(data, [], path)

        return RosdepLookup(rosdep_db, loader, override_entry=override_entry)

    def resolve_all(self, resources, installer_context):
        """
        Resolve all the rosdep dependencies for *resources* using *installer_context*.

        :param resources: list of resources (e.g. packages), ``[str]]``
        :param installer_context: :class:`InstallerContext`
        :returns: (resolutions, errors), ``({str: opaque}, {str: ResolutionError})``.  resolutions maps the installer keys
          to resolved objects.  Resolved objects are opaque but can be passed into the associated installer for processing.
          errors maps package names to an :exc:`ResolutionError` or :exc:`KeyError` exception.
        """
        resolutions = defaultdict(list)
        errors = {}
        for resource_name in resources:
            try:
                rosdep_keys = self.get_rosdeps(resource_name, implicit=True)
                if self.verbose:
                    print("resolve_all: resource [%s] requires rosdep keys [%s]"%(resource_name, ', '.join(rosdep_keys)))
                for rosdep_key in rosdep_keys:
                    try:
                        installer_key, resolution, dependencies = \
                                       self.resolve(rosdep_key, resource_name, installer_context)
                        resolutions[installer_key].append(resolution)
                        while dependencies:
                            depend_rosdep_key = dependencies.pop()
                            installer_key, resolution, more_dependencies = \
                                           self.resolve(depend_rosdep_key, resource_name, installer_context)
                            dependencies.extend(more_dependencies)
                            resolutions[installer_key].append(resolution)

                    except ResolutionError as e:
                        errors[resource_name] = e
            except ResourceNotFound as e:
                errors[resource_name] = e

        # check for dependencies
        for installer_key, val in resolutions.items(): #py3k
            for d in dependencies:
                self.install_rosdep(d, rdlp, default_yes, execute)

        # consolidate resolutions 
        for installer_key, val in resolutions.items(): #py3k
            installer = installer_context.get_installer(installer_key)
            resolutions[installer_key] = installer.unique(*val)

        return resolutions, errors

    def resolve(self, rosdep_key, resource_name, installer_context):
        """
        Resolve a :class:`RosdepDefinition` for a particular
        os/version spec.

        :param resource_name: resource (e.g. ROS package) to resolve key within
        :param rosdep_key: rosdep key to resolve
        :param os_name: OS name to use for resolution
        :param os_version: OS name to use for resolution

        :returns: *(installer_key, resolution, dependencies)*, ``(str,
          [opaque], [str])``.  *resolution* are the system
          dependencies for the specified installer.  The value is an
          opaque list and meant to be interpreted by the
          installer. *dependencies* is a list of rosdep keys that the
          definition depends on.

        :raises: :exc:`ResolutionError` If *rosdep_key* cannot be resolved for *resource_name* in *installer_context*
        :raises: :exc:`rospkg.ResourceNotFound` if *resource_name* cannot be located
        """
        os_name, os_version = installer_context.get_os_name_and_version()

        view = self.get_rosdep_view_for_resource(resource_name)
        if view is None:
            raise ResolutionError(rosdep_key, None, os_name, os_version, "[%s] does not have a rosdep view"%(resource_name))   
        try:
            definition = view.lookup(rosdep_key)
        except KeyError:
            rd_debug(view)
            raise ResolutionError(rosdep_key, None, os_name, os_version, "Cannot locate rosdep definition for [%s]"%(rosdep_key))

        # check cache: the main motivation for the cache is that
        # source rosdeps are expensive to resolve
        if rosdep_key in self._resolve_cache:
            cache_value = self._resolve_cache[rosdep_key]
            cache_os_name = cache_value[0]
            cache_os_version = cache_value[1]
            cache_view_name = cache_value[2]
            if cache_os_name == os_name and \
                   cache_os_version == os_version and \
                   cache_view_name == view.name:
                return cache_value[3:]

        # get the rosdep data for the platform
        try:
            installer_keys = installer_context.get_os_installer_keys(os_name)
            default_key = installer_context.get_default_os_installer_key(os_name)
        except KeyError:
            raise ResolutionError(rosdep_key, definition.data, os_name, os_version, "Unsupported OS [%s]"%(os_name))
        installer_key, rosdep_args_dict = definition.get_rule_for_platform(os_name, os_version, installer_keys, default_key)

        # resolve the rosdep data for the platform
        try:
            installer = installer_context.get_installer(installer_key)
        except KeyError:
            raise ResolutionError(rosdep_key, definition.data, os_name, os_version, "Unsupported installer [%s]"%(installer_key))
        resolution = installer.resolve(rosdep_args_dict)
        dependencies = installer.get_depends(rosdep_args_dict)        

        # cache value
        self._resolve_cache[rosdep_key] = os_name, os_version, view.name, installer_key, resolution, dependencies

        return installer_key, resolution, dependencies
        
    def _load_all_views(self):
        """
        Load all available view keys.  In general, this is equivalent
        to loading all stacks on the package path.  If
        :exc:`InvalidRosdepData` errors occur while loading a view,
        they will be saved in the *errors* field.

        :raises: :exc:`RosdepInternalError` 
        """
        for resource_name in self.loader.get_loadable_views():
            try:
                self._load_view_dependencies(resource_name)
            except ResourceNotFound as e:
                self.errors.append(e)
            except InvalidRosdepData as e:
                self.errors.append(e)
        
    def _load_view_dependencies(self, view_key):
        """
        Initialize internal :exc:`RosdepDatabase` on demand.  Not
        thread-safe.

        :param view_key: name of view to load dependencies for.
        
        :raises: :exc:`rospkg.ResourceNotFound` If view cannot be located
        :raises: :exc:`InvalidRosdepData` if view's data is invaid
        :raises: :exc:`RosdepInternalError`
        """
        rd_debug("_load_view_dependencies[%s]"%(view_key))
        db = self.rosdep_db
        if db.is_loaded(view_key):
            return
        try:
            self.loader.load_view(view_key, db, verbose=self.verbose)
            entry = db.get_view_data(view_key)
            rd_debug("_load_view_dependencies[%s]: %s"%(view_key, entry.view_dependencies))            
            for d in entry.view_dependencies:
                self._load_view_dependencies(d)
        except InvalidRosdepData:
            # mark view as loaded: as we are caching, the valid
            # behavior is to not attempt loading this stack ever
            # again.
            db.mark_loaded(view_key)
            # re-raise
            raise
        except KeyError as e:
            raise RosdepInternalError(e)
    
    def create_rosdep_view(self, view_name, view_keys):
        """
        :raises: :exc:`RosdepConflict` If view cannot be created due to conflicting definitions.
        """
        # Create view and initialize with dbs from all of the
        # dependencies. 
        view = RosdepView(view_name)

        db = self.rosdep_db
        for view_key in view_keys:
            db_entry = db.get_view_data(view_key)
            view.merge(db_entry)

        # ~/.ros/rosdep.yaml has precedence
        if self.override_entry is not None:
            view.merge(self.override_entry, override=True)
        return view
    
    def get_rosdep_view_for_resource(self, resource_name):
        """
        Get a :class:`RosdepView` for a specific ROS resource *resource_name*.
        Views can be queries to resolve rosdep keys to
        definitions.

        :param resource_name: Name of ROS resource (e.g. stack,
          package) to create view for, ``str``.

        :returns: :class:`RosdepView` for specific ROS resource
          *resource_name*, or ``None`` if no view is associated with this resource.
        
        :raises: :exc:`RosdepConflict` if view cannot be created due
          to conflict rosdep definitions.
        :raises: :exc:`rospkg.ResourceNotFound` if *view_key* cannot be located
        :raises: :exc:`RosdepInternalError` 
        """
        view_key = self.loader.get_view_key(resource_name)
        if not view_key:
            #NOTE: this may not be the right behavior and this happens
            #for packages that are not in a stack.
            return None
        return self.get_rosdep_view(view_key)
        
    def get_rosdep_view(self, view_key):
        """
        Get a :class:`RosdepView` associated with *view_key*.  Views
        can be queries to resolve rosdep keys to definitions.

        :param view_key: Name of rosdep view (e.g. ROS stack name), ``str``
        
        :raises: :exc:`RosdepConflict` if view cannot be created due
          to conflict rosdep definitions.
        :raises: :exc:`rospkg.ResourceNotFound` if *view_key* cannot be located
        :raises: :exc:`RosdepInternalError` 
        """
        if view_key in self._view_cache:
            return self._view_cache[view_key]

        # lazy-init
        self._load_view_dependencies(view_key)

        # use dependencies to create view
        try:
            dependencies = self.rosdep_db.get_view_dependencies(view_key)
        except KeyError as e:
            # convert to ResourceNotFound.  This should be decoupled
            # in the future
            raise ResourceNotFound(str(e.args[0]))
        view = self.create_rosdep_view(view_key, [view_key] + dependencies)
        self._view_cache[view_key] = view
        return view

    def get_views_that_define(self, rosdep_name):
        """
        Locate all views that directly define *rosdep_name*.  A
        side-effect of this method is that all available rosdep files
        in the configuration will be loaded into memory.

        Error state from single-stack failures
        (e.g. :exc:`InvalidRosdepData`, :exc:`ResourceNotFound`) are
        not propagated.  Caller must check
        :meth:`RosdepLookup.get_errors` to check for single-stack
        error state.  Error state does not reset -- it accumulates.

        :param rosdep_name: name of rosdep to lookup
        :returns: list of (stack_name, origin) where rosdep is defined.

        :raises: :exc:`RosdepInternalError` 
        """
        #TODOXXX: change this to return errors object so that caller cannot ignore
        self._load_all_views()
        db = self.rosdep_db
        retval = []
        for view_name in db.get_view_names():
            entry = db.get_view_data(view_name)
            # not much abstraction in the entry object
            if rosdep_name in entry.rosdep_data:
                retval.append((view_name, entry.origin))

        if self.override_entry is not None and \
               rosdep_name in self.override_entry.rosdep_data:
            retval.append((OVERRIDE_ENTRY, self.override_entry.origin))
        else:
            # for branch coverage verification
            pass
            
        return retval
