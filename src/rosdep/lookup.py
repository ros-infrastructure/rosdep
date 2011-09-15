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
            raise ResolutionError(rosdep_key, data, os_name, os_version, "No definition for OS [%s]"%(os_name))
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
                        raise ResolutionError(rosdep_key, self.data, os_name, os_version, "No definition for OS version [%s]"%(os_name))
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
        return """%s
\trosdep key : %s
\tOS name    : %s
\tOS version : %s
\tData: %s"""%(self.args[0], self.rosdep_key, self.os_name, self.os_version, self.rosdep_data)

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
        return """Rules for %s do not match:
\t%s [%s]
\t%s [%s]"""%(self.definition_name, self.definition1.data, self.definition1.origin, self.definition2.data, self.definition2.origin)
    
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
                # original rosdep implementation had ability
                # to record multiple sources; this does not.
                if definition.data != dep_data:
                    raise RosdepConflict(dep_name, definition, update_definition) 

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
        self._resolve_cache = {} # {str : (os_name, os_version, installer_key, resolution)}
        
        # ROS_HOME/rosdep.yaml can override 
        self.override_entry  = override_entry

        # some APIs that deal with the entire environment save errors
        # in to self.errors instead of raising them in order to be
        # robust to single-stack faults.
        self.errors = []

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
    
    def get_rosdeps(self, package):
        """
        Get rosdeps that this package directly requires.

        :returns: list of rosdep names, ``[str]``
        """
        m = self.loader.get_package_manifest(package)
        return [d.name for d in m.rosdeps]

    def get_packages_that_need(self, rosdep_name):
        """
        :param rosdep_name: name of rosdep dependency
        
        :returns: list of package names that require rosdep, ``[str]``
        """
        return [p for p in self.loader.get_loadable_packages() if rosdep_name in self.get_rosdeps(p)]

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

    def resolve_all(self, packages, installer_context):
        """
        Resolve all the rosdep dependencies for *packages* using *installer_context*.

        :param packages: list of ROS packages, ``[str]]``
        :param installer_context: :class:`InstallerContext`
        :returns: (resolutions, errors), ``({str: opaque}, {str: ResolutionError})``.  resolutions maps the installer keys
          to resolved objects.  Resolved objects are opaque but can be passed into the associated installer for processing.
          errors maps package names to an :exc:`ResolutionError` or :exc:`KeyError` exception.
        """
        resolutions = defaultdict(list)
        errors = {}
        for package_name in packages:
            rosdep_keys = self.get_rosdeps(package_name)
            for rosdep_key in rosdep_keys:
                try:
                    installer_key, resolution = self.resolve(rosdep_key, package_name, installer_context)
                    resolutions[installer_key].append(resolution)

                    # check and resolve dependencies
                    installer = installer_context.get_installer(installer_key)
                    dependencies = installer.get_depends()
                    for depend_rosdep_key in dependencies:
                        installer_key, resolution = self.resolve(depend_rosdep_key, package_name, installer_context)
                        resolutions[installer_key].append(resolution)
                        
                except ResolutionError as e:
                    errors[package_name] = e
                except KeyError as e:
                    rd_debug(traceback.format_exc())
                    errors[package_name] = e

        # check for dependencies
        for installer_key, val in resolutions.items(): #py3k

            for d in dependencies:
                self.install_rosdep(d, rdlp, default_yes, execute)

            
        # consolidate resolutions 
        for installer_key, val in resolutions.items(): #py3k
            installer = installer_context.get_installer(installer_key)
            resolutions[installer_key] = installer.unique(*val)

        return resolutions, errors

    def resolve(self, rosdep_key, package_name, installer_context):
        """
        Resolve a :class:`RosdepDefinition` for a particular
        os/version spec.

        :param package_name: package to resolve key within
        :param rosdep_key: rosdep key to resolve
        :param os_name: OS name to use for resolution
        :param os_version: OS name to use for resolution

        :raises: :exc:`ResolutionError` If *rosdep_key* cannot be resolved for *package_name* in *installer_context*
        :raises: :exc:`KeyError` If ROS package *package_name* does not exist
        :raises: :exc:`rospkg.ResourceNotFound` if *package_name* cannot be located
        """
        os_name, os_version = installer_context.get_os_name_and_version()

        # check cache
        if rosdep_key in self._resolve_cache:
            cache_value = self._resolve_cache[rosdep_key]
            cache_os_name = cache_value[0]
            cache_os_version = cache_value[1]
            if cache_os_name == os_name and cache_os_version == os_version:
                return cache_value[2], cache_value[3]
            
        view = self.get_package_rosdep_view(package_name)
        try:
            definition = view.lookup(rosdep_key)
        except KeyError:
            rd_debug(view)
            raise ResolutionError(rosdep_key, None, os_name, os_version, "No definition for OS [%s]"%(os_name))

        # get the rosdep data for the platform
        try:
            installer_keys = installer_context.get_os_installer_keys(os_name)
            default_key = installer_context.get_default_os_installer_key(os_name)
        except KeyError:
            raise ResolutionError(rosdep_key, definition.data, os_name, os_version, "Unsupported OS [%s]"%(os_name))
        installer_key, rosdep_args_dict = definition.get_rule_for_platform(os_name, os_version, installer_keys, default_key)

        # resolve the rosdep data for the platform
        installer = installer_context.get_installer(installer_key)
        resolution = installer.resolve(rosdep_args_dict)

        # cache value
        self._resolve_cache[rosdep_key] = os_name, os_version, installer_key, resolution

        return installer_key, resolution
        
    def _load_all_stacks(self):
        """
        Load all available stacks.  In general, this is equivalent to
        loading all stacks on the package path.  If
        :exc:`InvalidRosdepData` errors occur while loading a stack,
        they will be saved in the *errors* field.  

        :raises: :exc:`RosdepInternalError` 
        """
        for stack_name in self.loader.get_loadable_stacks():
            try:
                self._load_stack_dependencies(stack_name)
            except ResourceNotFound as e:
                raise RosdepInternalError(e)
            except InvalidRosdepData as e:
                self.errors.append(e)
        
    def _load_stack_dependencies(self, stack_name):
        """
        Initialize internal :exc:`RosdepDatabase` on demand.  Not
        thread-safe.

        :raises: :exc:`rospkg.ResourceNotFound` if stack cannot be located
        :raises: :exc:`InvalidRosdepData` if stack's data is invaid
        :raises: :exc:`RosdepInternalError`
        """
        rd_debug("load_stack_dependencies[%s]"%(stack_name))
        db = self.rosdep_db
        if db.is_loaded(stack_name):
            return
        try:
            self.loader.load_stack(stack_name, db)
            entry = db.get_stack_data(stack_name)
            rd_debug("load_stack_dependencies[%s]: %s"%(stack_name, entry.stack_dependencies))            
            for d in entry.stack_dependencies:
                self._load_stack_dependencies(d)
        except InvalidRosdepData:
            # mark stack as loaded: as we are caching, the valid
            # behavior is to not attempt loading this stack ever
            # again.
            db.mark_loaded(stack_name)
            # re-raise
            raise
        except KeyError as e:
            raise RosdepInternalError(e)
    
    def create_rosdep_view(self, view_name, stack_names):
        """
        :raises: :exc:`RosdepConflict` If view cannot be created due to conflicting definitions.
        """
        # Create view and initialize with dbs from all of the
        # dependencies. 
        view = RosdepView(view_name)

        db = self.rosdep_db
        for stack_name in stack_names:
            db_entry = db.get_stack_data(stack_name)
            view.merge(db_entry)

        # ~/.ros/rosdep.yaml has precedence
        if self.override_entry is not None:
            view.merge(self.override_entry, override=True)
        return view
    
    def get_package_rosdep_view(self, package_name):
        """
        Get a :class:`RosdepView` for a specific ROS package
        *package_name*.  Views can be queries to resolve rosdep keys
        to definitions.

        :raises: :exc:`RosdepConflict` if view cannot be created due
          to conflict rosdep definitions.
        :raises: :exc:`rospkg.ResourceNotFound` if *package_name* cannot be located
        :raises: :exc:`RosdepInternalError` 
        """
        stack_name = self.loader.stack_of(package_name)
        if stack_name:
            return self.get_stack_rosdep_view(stack_name)
        else:
            #TODOXXX: recursively compute all stacks that this package depends on
            #view = self.create_rosdep_view(package_name, dependencies)
            raise NotImplemented("TODO")
        
    def get_stack_rosdep_view(self, stack_name):
        """
        Get a :class:`RosdepView` for a specific ROS stack
        *stack_name*.  Views can be queries to resolve rosdep keys to
        definitions.

        :raises: :exc:`RosdepConflict` if view cannot be created due
          to conflict rosdep definitions.
        :raises: :exc:`rospkg.ResourceNotFound` if *stack_name* cannot be located
        :raises: :exc:`RosdepInternalError` 
        """
        if stack_name in self._view_cache:
            return self._view_cache[stack_name]

        # lazy-init
        self._load_stack_dependencies(stack_name)

        # use stack dependencies to create view
        dependencies = self.rosdep_db.get_stack_dependencies(stack_name)
        view = self.create_rosdep_view(stack_name, [stack_name] + dependencies)
        self._view_cache[stack_name] = view
        return view

    def get_stacks_that_define(self, rosdep_name):
        """
        Locate all stacks that define *rosdep_name*.  A side-effect of
        this method is that all available rosdep files in the
        configuration will be loaded into memory.

        Error state from single-stack failures
        (e.g. :exc:`InvalidRosdepData`) are not propagated.  Caller
        must check :meth:`RosdepLookup.get_errors` to check for single-stack
        error state.  Error state does not reset -- it accumulates.

        :param rosdep_name: name of rosdep to lookup
        :returns: list of (stack_name, origin) where rosdep is defined.

        :raises: :exc:`RosdepInternalError` 
        """
        #TODOXXX: change this to return errors object so that caller cannot ignore
        self._load_all_stacks()
        db = self.rosdep_db
        retval = []
        for stack_name in db.get_stack_names():
            entry = db.get_stack_data(stack_name)
            # not much abstraction in the entry object
            if rosdep_name in entry.rosdep_data:
                retval.append((stack_name, entry.origin))

        if self.override_entry is not None and \
               rosdep_name in self.override_entry.rosdep_data:
            retval.append((OVERRIDE_ENTRY, self.override_entry.origin))
        else:
            # for branch coverage verification
            pass
            
        return retval
