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

# Author Tully Foote, Ken Conley

import os

from rospkg.os_detect import OsDetect, OsDetector, OS_DEBIAN, OS_UBUNTU, OS_MINT

from .pip import PIP_INSTALLER
from .source import SOURCE_INSTALLER
from ..installers import PackageManagerInstaller
from ..shell_utils import create_tempfile_from_string_and_execute, read_stdout

# apt package manager key
APT_INSTALLER='apt'

def register_installers(context):
    context.set_installer(APT_INSTALLER, AptInstaller)

def register_debian(context):
    context.(OS_DEBIAN, APT_INSTALLER)
    context.add_os_installer(OS_DEBIAN, PIP_INSTALLER)
    context.add_os_installer(OS_DEBIAN, SOURCE_INSTALLER)
    context.set_default_os_installer(OS_DEBIAN, APT_INSTALLER)
    
def register_ubuntu(context):
    context.add_os_installer(OS_UBUNTU, APT_INSTALLER)
    context.add_os_installer(OS_UBUNTU, PIP_INSTALLER)
    context.add_os_installer(OS_UBUNTU, SOURCE_INSTALLER)
    context.set_default_os_installer(OS_UBUNTU, APT_INSTALLER)

def register_mint(context):
    # override mint detector with different version info
    detector = OsDetect().get_detector(OS_MINT)
    context.set_os_detector(OS_MINT, MintOsDetect(detector))
    
    context.add_os_installer(OS_MINT, APT_INSTALLER)
    context.add_os_installer(OS_MINT, PIP_INSTALLER)
    context.add_os_installer(OS_MINT, SOURCE_INSTALLER)
    context.set_default_os_installer(OS_MINT, APT_INSTALLER)
    
def dpkg_detect(pkgs):
    """ 
    Given a list of package, return the list of installed packages.
    """
    ret_list = []
    # this is mainly a hack to support version locking for eigen.
    # we strip version-locking syntax, e.g. libeigen3-dev=3.0.1-*.
    # our query does not do the validation on the version itself.
    version_lock_map = {}
    for p in pkgs:
        if '=' in p:
            version_lock_map[p.split('=')[0]] = p
        else:
            version_lock_map[p] = p
    cmd = ['dpkg-query', '-W', '-f=\'${Package} ${Status}\n\'']
    cmd.extend(version_lock_map.keys())

    std_out = read_stdout(cmd)
    std_out = std_out.replace('\'','')
    pkg_list = std_out.split('\n')
    for pkg in pkg_list:
        pkg_row = pkg.split()
        if len(pkg_row) == 4 and (pkg_row[3] =='installed'):
            ret_list.append( pkg_row[0])
    return [version_lock_map[r] for r in ret_list]        

class AptInstaller(PackageManagerInstaller):
    """ 
    An implementation of the Installer for use on debian style
    systems.
    """
    def __init__(self, rosdep_rule_arg_dict):
        packages = rosdep_rule_arg_dict.get("packages", "")
        if type(packages) == type("string"):
            packages = packages.split()
        super(AptInstaller, self).__init__(packages, dpkg_detect)

    def generate_package_install_command(self, default_yes=False, execute=True, display=True):
        script = '!#/bin/bash\n#no script'
        packages_to_install = self.get_packages_to_install()
        if not packages_to_install:
            script =  "#!/bin/bash\n#No Packages to install"
        if default_yes:
            script = "#!/bin/bash\n#Packages %s\nsudo apt-get install -y "%packages_to_install + ' '.join(packages_to_install)        
        else:
            script =  "#!/bin/bash\n#Packages %s\nsudo apt-get install "%packages_to_install + ' '.join(packages_to_install)

        if execute:
            return create_tempfile_from_string_and_execute(script)
        elif display:
            print "To install packages: %s would have executed script\n{{{\n%s\n}}}"%(packages_to_install, script)
        return False

class MintOsDetect(OsDetect):
    """
    Special Mint OS detector that overrides version number information.
    """

    version_map = {'11':'11.04',
                   '10':'10.10',
                   '9':'10.04',
                   '8':'9.10', 
                   '7':'9.04',
                   '6':'8.10',
                   '5':'8.04'}

    def __init__(self, base_detector):
        self._detector = detector
    
    def is_os(self):
        return self._detector.is_os()
        
    def get_version(self):
        # remap version
        return self.version_map[self._detector.get_version()]
    
