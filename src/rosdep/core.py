# Copyright (c) 2009, Willow Garage, Inc.
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

import os
import sys
import yaml
import time

def rd_debug(s):
    if "ROSDEP_DEBUG" in os.environ:
        print(s)
    
    def get_version_from_yaml(self, rosdep_name, os_specific, source_path):
        """
        Helper function for get_os_from_yaml to parse if version is required.  
        @return The os (and version specific if required) local package name
        """
        
        # This is a map to provide backwards compatability for rep111 changes.  
        # See http://www.ros.org/reps/rep-0111.html for more info. 
        rep111version_map = {'lucid':'10.04', 'maverick':'10.10', 'natty':'11.04'}

        if type(os_specific) == type("String"): # It's just a single string 
            return os_specific
        if self.os_version in os_specific: # if it is a version key, just return it
            return os_specific[self.os_version]
        if self.os_version in rep111version_map: # check for rep 111 special versions 
            rep_version = rep111version_map[self.os_version]
            if rep_version in os_specific:
                return os_specific[rep_version]
        if type(os_specific) == type({}): # detected a map
            for k in os_specific.keys():
                if not k in self.installers:
                    print("Invalid identifier found [%s] when processing rosdep %s.  \n{{{\n%s\n}}}\n"%(k, rosdep_name, os_specific))
                    return False # If the map doesn't have a valid installer key reject it, it must be a version key
            # return the map 
            return os_specific
        else:
            print("Unknown formatting of os_specific", os_specific)
            return False                    

class RosdepException(Exception):
    pass

class RosdepInstaller:
    def __init__(self, packages, robust=False):
        os_list = TODO
        # Make sure that these classes are all well formed.  
        for o in os_list:
            if not isinstance(o, rosdep.base_rosdep.RosdepBaseOS):
                raise RosdepException("Class [%s] not derived from RosdepBaseOS"%o.__class__.__name__)
        # Detect the OS on which this program is running. 
        self.osi = roslib.os_detect.OSDetect(os_list)
        self.yc = YamlCache(self.osi.get_name(), self.osi.get_version(), self.osi.get_os().installers)
        self.packages = packages
        rp = roslib.packages.ROSPackages()
        self.rosdeps = rp.rosdeps(packages)
        self.robust = robust
            
    def get_packages_and_scripts(self, rdlp_cache=None):
        """
        @param rdlp_cache: cache of L{RosdepLookupPackage} instances.  Instances must have been created
        with self.osi.get_name(), self.osi.get_version(), and self.yc.
        @type  rdlp_cache: {str: RosdepLookupPackage}
        """
        if len(self.packages) == 0:
            return ([], [])
        native_packages = []
        scripts = []
        failed_rosdeps = []
        start_time = time.time()
        rd_debug("Generating package list and scripts for %d packages.  This may take a few seconds..."%len(self.packages))
        if rdlp_cache == None:
            rdlp_cache = {}
            
        for r, packages in self.get_rosdeps(self.packages).iteritems():
            # use first package for lookup rules
            p = packages[0]
            if p in rdlp_cache:
                rdlp = rdlp_cache[p]
            else:
                rdlp = RosdepLookupPackage(self.osi.get_name(), self.osi.get_version(), p, self.yc)
                rdlp_cache[p] = rdlp
            specific = rdlp.lookup_rosdep(r)
            if specific:
                if type(specific) == type({}):
                    rd_debug("%s NEW TYPE, SKIPPING"%r)
                elif len(specific.split('\n')) == 1:
                    for pk in specific.split():
                        native_packages.append(pk)
                else:
                    scripts.append(specific)
            else:
                failed_rosdeps.append(r)

        if len(failed_rosdeps) > 0:
            if not self.robust:
                raise RosdepException("ABORTING: Rosdeps %s could not be resolved"%failed_rosdeps)
            else:
                print("WARNING: Rosdeps %s could not be resolved"%failed_rosdeps, file=sys.stderr)

        time_delta = (time.time() - start_time)
        rd_debug("Done loading rosdeps in %f seconds, averaging %f per rosdep."%(time_delta, time_delta/len(self.packages)))

        return (list(set(native_packages)), list(set(scripts)))
        
    def satisfy(self):
        """ 
        return a list of failed rosdeps and print what would have been done to install them
        """
        return self.check(display = True)

    def check(self, display = False):
        """ 
        Return a list of failed rosdeps
        """
        failed_rosdeps = []
        rdlp_cache = {}
        try:
            native_packages, scripts = self.get_packages_and_scripts(rdlp_cache=rdlp_cache)
            num_scripts = len(scripts)
            if num_scripts > 0:
                print("Found %d scripts.  Cannot check scripts for presence. rosdep check will always fail."%num_scripts)
                failure = False
                if display == True:
                    for s in scripts:
                        print("Script:\n{{{\n%s\n}}}"%s)
        except RosdepException as e:
            print("error in processing scripts", e, file=sys.stderr)

        for r, packages in self.get_rosdeps(self.packages).iteritems():
            # use first package for lookup rule
            p = packages[0]
            if p in rdlp_cache:
                rdlp = rdlp_cache[p]
            else:
                rdlp = RosdepLookupPackage(self.osi.get_name(), self.osi.get_version(), p, self.yc)
                rdlp_cache[p] = rdlp
            if not self.install_rosdep(r, rdlp, default_yes=False, execute=False, display=display):
                failed_rosdeps.append(r)

        return failed_rosdeps

    def install(self, include_duplicates, default_yes, execute=True):
        failure = False

        for r, packages in self.get_rosdeps(self.packages).iteritems():
            # use the first package as the lookup rule
            p = packages[0]
            rdlp = RosdepLookupPackage(self.osi.get_name(), self.osi.get_version(), p, self.yc)
            if not self.install_rosdep(r, rdlp, default_yes, execute):
                failure = True
                if not self.robust:
                    return "failed to install %s"%r

        if failure:
            return "Rosdep install failed"
        return None
        

    def install_rosdep(self, rosdep_name, rdlp, default_yes, execute, display=True):
        """
        Install a single rosdep given it's name and a lookup table. 
        @param default_yes Add a -y to the installation call
        @param execute If True execute, if false, don't execute just print
        @return If the install was successful
        """
        rd_debug("Processing rosdep %s in install_rosdep method"%rosdep_name)
        rosdep_dict = rdlp.lookup_rosdep(rosdep_name)
        if not rosdep_dict:
            return False
        mode = 'default'
        installer = None
        if type(rosdep_dict) != type({}):
            rd_debug("OLD TYPE BACKWARDS COMPATABILITY MODE", rosdep_dict)

            if len(rosdep_dict.split('\n')) > 1:
                raise RosdepException( "SCRIPT UNIMPLEMENTED AT THE MOMENT TODO")

            installer = self.osi.get_os().get_installer('default')
            packages = rosdep_dict.split()
            arg_map = {}
            arg_map['packages'] = packages
            rosdep_dict = {} #override old values
            rosdep_dict['default'] = arg_map 

        else:
            modes = rosdep_dict.keys()
            if len(modes) != 1:
                print("ERROR: only one mode allowed, rosdep %s has mode %s"%(rosdep_name, modes))
                return False
            else:
                mode = modes[0]

        rd_debug("rosdep mode:", mode)
        installer = self.osi.get_os().get_installer(mode)
        
        if not installer:
            raise RosdepException( "Rosdep failed to get an installer for mode %s"%mode)
            
        my_installer = installer(rosdep_dict[mode])

        # Check if it's already there
        if my_installer.check_presence():
            rd_debug("rosdep %s already present"%rosdep_name)
            return True
        else:
            rd_debug("rosdep %s not detected.  It will be installed"%rosdep_name)
        
        # Check for dependencies
        dependencies = my_installer.get_depends()
        for d in dependencies:
            self.install_rosdep(d, rdlp, default_yes, execute)

        result = my_installer.generate_package_install_command(default_yes, execute, display)
        if result:
            print("successfully installed %s"%(rosdep_name))
            if not my_installer.check_presence():
                print("rosdep %s failed check-presence-script after installation"%(rosdep_name))
                return False

        elif execute:
            print ("Failed to install %s!"%(rosdep_name))
        return result

