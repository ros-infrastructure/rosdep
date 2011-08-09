#!/usr/bin/env python
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

# Author Tully Foote/tfoote@willowgarage.com

from __future__ import print_function

import os
import sys
import subprocess

from ..installers import Installer

# pip package manager key
PIP = 'pip'

def register_installers(context):
    context.register_installer(PIP, PipInstaller)

def pip_detect(self, pkgs):
    """ 
    Given a list of package, return the list of installed packages.
    """
    cmd = ['pip', 'freeze']
    pop = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (std_out, std_err) = pop.communicate()
    pkg_list = std_out.split('\n')

    ret_list = []
    for pkg in pkg_list:
        pkg_row = pkg.split("==")
        #print(pkg_row)
        if pkg_row[0] in pkgs:
            ret_list.append( pkg_row[0])
    return ret_list

class PipInstaller(Installer):
    """ 
    An implementation of the Installer for use on debian style
    systems.
    """

    def __init__(self, rosdep_rule_arg_dict):
        packages = rosdep_rule_arg_dict.get("packages", "")
        if type(packages) == type("string"):
            packages = packages.split()
        self.depends = rosdep_rule_arg_dict.get("depends", [])
        self.packages = packages

    def get_packages_to_install(self):
        return list(set(self.packages) - set(pip_detect(self.packages)))

    def check_presence(self):
        return len(self.get_packages_to_install()) == 0

    def get_depends(self):
        #todo verify type before returning
        return self.depends

    def generate_package_install_command(self, default_yes = False, execute = True, display = True):
        packages_to_install = self.get_packages_to_install()
        script = '!#/bin/bash\n#no script'
        if not packages_to_install:
            script =  "#!/bin/bash\n#No PIP Packages to install"
        #if default_yes:
        #    script = "#!/bin/bash\n#Packages %s\nsudo apt-get install -U "%packages_to_install + ' '.join(packages_to_install)        
        #else:
        script =  "#!/bin/bash\n#Packages %s\nsudo pip install -U "%packages_to_install + ' '.join(packages_to_install)

        if execute:
            return create_tempfile_from_string_and_execute(script)
        elif display:
            print("To install packages: %s would have executed script\n{{{\n%s\n}}}"%(packages_to_install, script))
        return False

