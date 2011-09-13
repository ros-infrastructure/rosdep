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

def rd_debug(s):
    if "ROSDEP_DEBUG" in os.environ:
        print(s)
    
class InstallFailed(Exception):
    pass

class RosdepInstaller:

    def __init__(self, lookup):
        self.lookup = lookup
        
    def check(self, packages, verbose=False):
        """ 
        Return a list of failed rosdeps
        """
        failed_rosdeps = []
        rdlp_cache = {}

        # this logic is wrong: it should go through package by
        # package, as each package has a unique view.  it should
        # resolve within that packages/stacks scope.  After it has
        # collected all resolutions, it can unique() them, and then it
        # can install them.
        
        for r, packages in self.get_rosdeps(packages).iteritems():
            # use first package for lookup rule
            p = packages[0]
            if p in rdlp_cache:
                rdlp = rdlp_cache[p]
            else:
                rdlp = RosdepLookupPackage(self.osi.get_name(), self.osi.get_version(), p, self.yc)
                rdlp_cache[p] = rdlp
            if not self.install_rosdep(r, rdlp, interactive=True, simulate=True, verbose=verbose):
                failed_rosdeps.append(r)

        return failed_rosdeps

    def install(self, interactive=True, simulate=False, continue_on_error=False):
        """
        :param interactive: (optional) If ``False``, suppress interactive prompts (e.g. by passing '-y' to ``apt``).  
        :param simulate: (optional) If ``False`` simulate installation without actually executing.
        :raises: :exc:`InstallFailed` if any rosdeps fail to install and *continue_on_error* is ``False``.
        :raises: :exc:`MultipleInstallsFailed` If *continue_on_error* is set and one or more installs failed.
        """
        failures = []

        for r, packages in self.get_rosdeps(self.packages).iteritems():
            # use the first package as the lookup rule
            p = packages[0]
            rdlp = RosdepLookupPackage(self.osi.get_name(), self.osi.get_version(), p, self.yc)
            try:
                self.install_rosdep(r, rdlp, interactive, simulate):
            except InstallFailed as e:
                if not continue_on_error:
                    raise
                else:
                    failures.append(e)
        if failures:
            raise MultipleInstallsFailed(failures)

    def install_rosdep(self, rosdep_name, rdlp, simulate=False, interactive=True, verbose=False):
        """
        Install a single rosdep given it's name and a lookup table. 

        :param interactive: (optional) If ``False``, suppress interactive prompts (e.g. by passing '-y' to ``apt``).  
        :param simulate: (optional) If ``False`` simulate installation without actually executing.
        :returns: ``True`` if the install was successful.
        """
        rd_debug("Processing rosdep %s in install_rosdep method"%rosdep_name)
        rosdep_dict = rdlp.lookup_rosdep(rosdep_name)
        if not rosdep_dict:
            return False
        mode = 'default'
        installer = None
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

        command = my_installer.get_install_command(default_yes, execute)
        if verbose or simulate:
            print("Installation command/script:\n"+80*'='+str(command)+80*'=')
        if not simulate:
            result = my_installer.execute_install_command(command)
            if result:
                print("successfully installed %s"%(rosdep_name))
                if not my_installer.is_installed(resolved):
                    print("rosdep %s failed check-presence-script after installation.\nResolved packages were %s"%(rosdep_name, resolved), file=sys.stderr)
                    return False

        elif execute:
            print ("Failed to install %s!"%(rosdep_name))
        return result

