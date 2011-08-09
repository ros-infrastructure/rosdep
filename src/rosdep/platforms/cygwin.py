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

# Tingfan Wu tingfan@gmail.com

import os
import subprocess

OS_NAME = 'cygwin'
APT_CYG = 'apt-cyg'

def register_installers(context):
    context.register_installer(APT_CYG, AptCygInstaller)
    
def register_cygwin(context):
    context.register_os_installer(OS_NAME, 'source')
    context.register_os_installer(OS_NAME, APT_CYG)
    context.set_default_os_installer(OS_NAME, APT_CYG)

def cygcheck_detect(p):
    cmd = ['cygcheck', '-c', p]
    pop = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (std_out, std_err) = pop.communicate()
    return (std_out.count("OK") > 0)

class AptCygInstaller(Installer):
    """
    An implementation of the Installer for use on cygwin-style
    systems.
    """

    def __init__(self, rosdep_rule_arg_dict):
        packages = rosdep_rule_arg_dict.get("packages", "")
        if type(packages) == type("string"):
            packages = packages.split()
        self.packages = packages

    def get_packages_to_install(self):
        return list(set(self.packages) - set(self.cygcheck_detect(self.packages)))

    def check_presence(self):
        return len(self.get_packages_to_install()) == 0

    def generate_package_install_command(self, default_yes = False, execute = True, display = True):
        return "#Packages\napt-cyg -m ftp://sourceware.org/pub/cygwinports install " + ' '.join(packages)        

if __name__ == '__main__':
    print "test cygcheck_detect(true)", cygcheck_detect('cygwin');
