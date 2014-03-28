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

import subprocess

from rospkg.os_detect import OS_RHEL, OS_FEDORA

from .pip import PIP_INSTALLER
from .source import SOURCE_INSTALLER
from ..installers import PackageManagerInstaller, TYPE_CODENAME
from ..shell_utils import read_stdout

# yum package manager key
YUM_INSTALLER='yum'

def register_installers(context):
    context.set_installer(YUM_INSTALLER, YumInstaller())

def register_platforms(context):
    register_fedora(context)
    register_rhel(context)
    
def register_fedora(context):
    context.add_os_installer_key(OS_FEDORA, PIP_INSTALLER)
    context.add_os_installer_key(OS_FEDORA, YUM_INSTALLER)
    context.add_os_installer_key(OS_FEDORA, SOURCE_INSTALLER)
    context.set_default_os_installer_key(OS_FEDORA, YUM_INSTALLER)
    context.set_os_version_type(OS_FEDORA, TYPE_CODENAME)

def register_rhel(context):
    context.add_os_installer_key(OS_RHEL, PIP_INSTALLER)
    context.add_os_installer_key(OS_RHEL, YUM_INSTALLER)
    context.add_os_installer_key(OS_RHEL, SOURCE_INSTALLER)
    context.set_default_os_installer_key(OS_RHEL, YUM_INSTALLER)

def rpm_detect(packages, exec_fn=None):
    ret_list = []
    #cmd = ['rpm', '-q', '--qf ""']  # suppress output for installed packages
    cmd = ['rpm', '-q', '--whatprovides', '--qf', '[%{PROVIDES}\n]']  # output: "pkg_name" for installed, error text for not installed packages
    cmd.extend(packages)

    if exec_fn is None:
        exec_fn = read_stdout

    std_out = exec_fn(cmd)
    out_lines = std_out.split('\n')
    for line in out_lines:
        # if there is no space, it's not an error text -> it's installed
        if line and ' ' not in line:
            ret_list.append(line)
    return ret_list

class YumInstaller(PackageManagerInstaller):
    """
    This class provides the functions for installing using yum
    it's methods partially implement the Rosdep OS api to complement 
    the roslib.OSDetect API.
    """

    def __init__(self):
        super(YumInstaller, self).__init__(rpm_detect)

    def get_install_command(self, resolved, interactive=True, reinstall=False):
        packages = self.get_packages_to_install(resolved, reinstall=reinstall)
        if not packages:
            return []
        elif not interactive:
            return [['sudo', 'yum', '-y', '--skip-broken', 'install'] + packages]
        else:
            return [['sudo', 'yum', '--skip-broken', 'install'] + packages]

