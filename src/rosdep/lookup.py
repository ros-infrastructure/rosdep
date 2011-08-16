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

from .model import RosdepDatabase
from .rospkg_loader import RosPkgLoader

class RosdepDefinition:
    """
    Single rosdep dependency definition.  This data is stored as the
    raw dictionary definition for the dependency.

    See REP 111, 'Multiple Package Manager Support for Rosdep' for a
    discussion of this raw format.
    """
    
    def __init__(self, data, origin="<dynamic>"):
        """
        @param origin: string that indicates where data originates from (e.g. filename)
        """
        self.data = data
        self.origin = origin
    
class RosdepConflict(Exception):

    def __init__(self, definition_name, definition1, definition2):
        self.definition_name = definition_name
        self.definition1 = definition1
        self.definition2 = definition2
        
    def __str__(self):
        return """Rules for %s do not match:
\t%s [%s]
\t%s [%s]"""%(self.definition_name, self.definition1.data, self.definition1.origin, self.definition2.data, self.definition2.origin)
    
class RosdepView:
    """
    View of L{RosdepDatabase}.  Unlike L{RosdepDatabase}, which stores
    L{RosdepDatabaseEntry} data for all stacks, a view merges entries
    for a particular stack.  This view can then be queries to lookup
    and resolve individual rosdep dependencies.
    """
    
    def __init__(self, name):
        self.name = name
        self.rosdep_defs = {} # {str: RosdepDefinition}

    def lookup(self, rosdep_name):
        """
        @return L{RosdepDefinition}
        @raise KeyError
        """
        return self.rosdep_defs[rosdep_name]

    def keys(self):
        """
        Return list of rosdep names in this view
        """
        return self.rosdep_defs.keys()
        
    def merge(self, update_entry, override=False):
        """
        Merge rosdep database update into main database

        @raise RosdepConflict
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

    RosdepLookup caches data as it is loaded, so changes made on the
    filesystem will not be reflected if the rosdep information has
    already been loaded.
    """
    
    def __init__(self, rosdep_db, loader, default_os_name, default_os_version):
        """
        @type loader: RosdepLoader
        @type rosdep_db: RosdepDatabase
        """
        self.rosdep_db = rosdep_db
        self.loader = loader
        self.default_os_name = default_os_name
        self.default_os_version = default_os_version

        self._view_cache = {} # {str: {RosdepView}}

        # ROS_HOME/rosdep.yaml can override 
        self.ros_home_entry  = None #RosdepDatabaseEntry

    def get_rosdeps(self, package):
        """
        Get rosdeps that this package directly requires.

        @return: list of rosdep names, [str]
        """
        m = self.loader.get_package_manifest(package)
        return [d.name for d in m.rosdeps]

    def what_needs(self, rosdep_name):
        """
        @param rosdep_name: name of rosdep dependency
        
        @return: list of package names that require rosdep, [str]
        """
        return [p for p in self.loader.get_loadable_packages() if rosdep_name in self.get_rosdeps(p)]

    @staticmethod
    def create_from_rospkg(rospack=None, rosstack=None, ros_home=None,
                           os_name=None, os_version=None):
        """
        Create RosdepLookup based on current ROS package environment.

        @param rospack: (optional) Override L{RosPack} instance used
        to crawl ROS packages.
        
        @param rosstack: (optional) Override L{RosStack} instance used
        to crawl ROS stacks.
        
        @param os_name: (optional) OS name to use for view.  Defaults
        to default_os_name.

        @param os_version: (optional) OS version to use for view.
        Defaults to default_os_version.
        """
        # initialize the loader
        if rospack is None:
            rospack = RosPack()
        if rosstack is None:
            rosstack = RosStack()
        if ros_home is None:
            ros_home = get_ros_home()

        loader = RosPkgLoader(rospack=rospack, rosstack=rosstack)

        # detect the operating system
        if os_name is None or os_version is None:
            os_detect = OsDetect()
            if os_name is None:
                os_name = os_detect.get_name()
            if os_version is None:
                os_version = os_detect.get_version()

        rosdep_db = RosdepDatabase()
        
        # Load ros_home/rosdep.yaml, if present.  It will be used to
        # override individual stack views.
        path = os.path.join(ros_home, "rosdep.yaml")
        if os.path.exists(path):
            with open(path, 'r') as f:
                data = loader.load_rosdep_yaml(f.read(), path)
            self.ros_home_entry = RosdepDatabaseEntry(data, [], path)

        return RosdepLookup(rosdep_db, loader, os_name, os_version)

    def resolve_definition(self, os_name=None, os_version=None):
        """
        Resolve a L{RosdepDefinition} for a particular os/version spec.
        
        @param os_name: (optional) OS name to use for view.  Defaults
        to default_os_name.

        @param os_version: (optional) OS version to use for view.
        Defaults to default_os_version.
        """
        if os_name is None:
            os_name = self.default_os_name
        if os_version is None:
            os_version = self.default_os_version
        
        raise NotImplementedError("TODO")
        
    def _load_all_stacks(self):
        """
        Load all available stacks.  In general, this is equivalent to
        loading all stacks on the package path.
        """
        for stack_name in self.loader.get_loadable_stacks():
            _load_stack_dependencies(stack_name)
        
    def _load_stack_dependencies(self, stack_name):
        """
        Initialize internal RosdepDatabase on demand.  Not
        thread-safe.
        """
        db = self.rosdep_db
        if db.is_loaded(stack_name):
            return
        self.loader.load_stack(stack_name, db)
        entry = db.get_stack_data(stack_name)
        for d in entry.stack_dependencies:
            self._load_stack_dependencies(stack_name)
    
    def get_rosdep_view(self, stack_name):
        """
        Get a L{RosdepView} for a specific stack and OS combination.
        A view enables queries for a particular stack or package in
        that stack.

        @raise RosdepConflict: if view cannot be created due to
        conflict rosdep definitions.

        @raise KeyError: if stack or stack dependencies do not exist.
        """
        if stack_name in self._view_cache:
            return self._view_cache

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
        if self.ros_home_entry is not None:
            view.merge(self.ros_home_entry, override=True)

        self._view_cache[stack_name] = view
        return view

    def where_defined(self, rosdeps):
        raise NotImplementedError('porting')
        locations = {}
        self._load_all_stacks()

        for r in rosdeps:
            locations[r] = set()
            
        for rd in locations:
            output += "%s defined in %s"%(rd, locations[rd])
        return locations
