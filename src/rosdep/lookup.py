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

from rospkg import RosPack, RosStack, get_ros_home
from rospkg.os_detect import OsDetect

from .model import RosdepDatabase, RosdepDatabaseEntry, InvalidRosdepData
from .rospkg_loader import RosPkgLoader

# key for representing .ros/rosdep.yaml override entry
OVERRIDE_ENTRY = '.ros'

class RosdepDefinition:
    """
    Single rosdep dependency definition.  This data is stored as the
    raw dictionary definition for the dependency.

    See REP 111, 'Multiple Package Manager Support for Rosdep' for a
    discussion of this raw format.
    """
    
    def __init__(self, data, origin="<dynamic>"):
        """
        :param data: raw rosdep data for a single rosdep dependency, ``dict``
        :param origin: string that indicates where data originates from (e.g. filename)
        """
        self.data = data
        self.origin = origin
    
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
    
class RosdepView:
    """
    View of :class:`RosdepDatabase`.  Unlike :class:`RosdepDatabase`,
    which stores :class:`RosdepDatabaseEntry` data for all stacks, a
    view merges entries for a particular stack.  This view can then be
    queries to lookup and resolve individual rosdep dependencies.
    """
    
    def __init__(self, name):
        self.name = name
        self.rosdep_defs = {} # {str: RosdepDefinition}

    def lookup(self, rosdep_name):
        """
        :returns: :class:`RosdepDefinition`
        :raises: :exc:`KeyError`
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
            update_definition = RosdepDefinition(dep_data, update_entry.origin)
            if override or not dep_name in db:
                db[dep_name] = update_definition
            else:
                definition = db[dep_name]
                # original rosdep implementation had ability
                # to record multiple sources; this does not.
                if definition.data != dep_data:
                    raise RosdepConflict(dep_name, definition, update_definition) 

class RosdepLookup:
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

        # ROS_HOME/rosdep.yaml can override 
        self.override_entry  = override_entry

        # some APIs that deal with the entire environment save errors
        # in to self.errors instead of raising them in order to be
        # robust to single-stack faults.
        self.errors = []

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

    def resolve_definition(self, os_name, os_version):
        """
        Resolve a :class:`RosdepDefinition` for a particular
        os/version spec.
        """
        #TODO: self.override_entry
        raise NotImplementedError("TODO")
        
    def _load_all_stacks(self):
        """
        Load all available stacks.  In general, this is equivalent to
        loading all stacks on the package path.  If errors occur while
        loading a stack, they will be saved in the errors field.
        """
        for stack_name in self.loader.get_loadable_stacks():
            try:
                self._load_stack_dependencies(stack_name)
            except InvalidRosdepData as e:
                self.errors.append(e)
        
    def _load_stack_dependencies(self, stack_name):
        """
        Initialize internal :exc:`RosdepDatabase` on demand.  Not
        thread-safe.
        """
        db = self.rosdep_db
        if db.is_loaded(stack_name):
            return
        try:
            self.loader.load_stack(stack_name, db)
            entry = db.get_stack_data(stack_name)
            for d in entry.stack_dependencies:
                self._load_stack_dependencies(stack_name)
        except InvalidRosdepData:
            # mark stack as loaded: as we are caching, the valid
            # behavior is to not attempt loading this stack ever
            # again.
            db.mark_loaded(stack_name)
            # re-raise
            raise
    
    def get_rosdep_view(self, stack_name):
        """
        Get a :class:`RosdepView` for a specific stack and OS
        combination.  A view enables queries for a particular stack or
        package in that stack.

        :raises: :exc:`RosdepConflict` if view cannot be created due
          to conflict rosdep definitions.

        :raises: :exc:`KeyError` if stack or stack dependencies do not
         exist.
        """
        if stack_name in self._view_cache:
            return self._view_cache[stack_name]

        # lazy-init
        self._load_stack_dependencies(stack_name)

        # Create view and initialize with dbs from all of the
        # dependencies. 
        view = RosdepView(stack_name)

        db = self.rosdep_db
        dependencies = db.get_stack_dependencies(stack_name)
        for s in [stack_name] + dependencies:
            db_entry = db.get_stack_data(s)
            view.merge(db_entry)

        # ~/.ros/rosdep.yaml has precedence
        if self.override_entry is not None:
            view.merge(self.override_entry, override=True)

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
        """
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
