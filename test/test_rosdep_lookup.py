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

from __future__ import print_function

def test_RosdepDefinition():
    from rosdep.lookup import RosdepDefinition
    d = dict(a=1, b=2, c=3)
    def1 = RosdepDefinition(d)
    assert def1.data == d
    def2 = RosdepDefinition(d, 'file1.txt')
    assert def2.data == d
    assert def2.origin == 'file1.txt'
    
def test_RosdepConflict():
    from rosdep.lookup import RosdepConflict
    
    ex = RosdepConflict('foo', def1, def2)
    str_ex = str(ex)
    print(str_ex)
    assert def1.origin in str_ex
    assert def2.origin in str_ex
    
def test_RosdepView():
    from rosdep.lookup import RosdepView
    d = dict(a=1, b=2, c=3)
    view = RosdepView('common', d)
    try:
        view.lookup_rosdep(
    assert view.lookup_rosdep('a') == 1
    

    def merge(self, update, override=False):
        """
        Merge rosdep database update into main database

        @raise RosdepConflict
        """
        db = self.rosdep_data
        for rosdep_name, update_definition in db_update.items():
            rosdep_entry = db_update[key]
            if override or not key in db:
                db[key] = update_definition
            else:
                definition = db[key]
                # original rosdep implementation had ability
                # to record multiple sources; this does not.
                if definition.data != update_definition.data:
                    raise RosdepConflict(rosdep_name, definition, update_definition)        

class RosdepLookup:
    
    def __init__(self, rosdep_db, loader, default_os_name, default_os_version):
        """
        @type loader: RosdepLoader
        @type rosdep_db: RosdepDatabase
        """
        self.rosdep_db = rosdep_db
        self.loader = loader
        self.default_os_name = default_os_name
        self.default_os_version = default_os_version

        self._view_cache = {} # {str: {rosdep_data}}

    def get_rosdep_view(self, stack_name, os_name=None, os_version=None):
        if not self.rosdeb_db.is_loaded(stack_name):
            self.loader.load_stack(stack_name)

        # load combined view for stack
        rosdep_data = self.rosdeb_db.get_stack_view(stack_name)

        # return API based on this view
        return RosdepView(stack_name, rosdep_data, os_name, os_version)

    def get_rosdeps(self, package):
        """
        Get list of rosdep names that this package directly requires.
        """
        m = self.loader.load_package_manifest(package)
        return [d.name for d in m.rosdeps]

    def what_needs(self, rosdep_args):
        raise NotImplemented
        packages = []
        for p in roslib.packages.list_pkgs():
            rosdeps_needed = self.get_rosdep0(p)
            matches = [r for r in rosdep_args if r in rosdeps_needed]
            for r in matches:
                packages.append(p)
                
        return packages

    @staticmethod
    def create_from_rospkg(self):
        """
        Create RosdepLookup based on current ROS package environment.
        """
        rosdep_db = RosdepDatabase()
        loader = RosPkgLoader()
        
        os_detect = OsDetect()
        os_name = os_detect.get_name()
        os_version = os_detect.get_version()

        # TODO: implement
        if 0:
            # Override with ros_home/rosdep.yaml if present
            ros_home = roslib.rosenv.get_ros_home()
            path = os.path.join(ros_home, "rosdep.yaml")
            self._insert_map(self.parse_yaml(path), path, override=True)

        return RosdepLookup(rosdep_db, loader, os_name, os_version)

    def get_stack_view(self, stack_name):
        """
        @return: computed rosdep database for given stack
        
        @raise KeyError: if stack_name is not in database
        """
        if stack_name in self._view_cache:
            return self._view_cache

        db_entry = self.get_stack_data(stack_name)
        rosdep_data = db_entry.rosdep_data.copy()

        view = RosdepView(stack_name, rosdep_data)

        for d in db_entry.stack_dependencies:
            view.merge(self.get_stack_db(d))
        self._view_cache[stack_name] = d
        return d

