#!/usr/bin/env python
# Copyright (c) 2010, Willow Garage, Inc.
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

# Original from cygwin.py by Tingfan Wu tingfan@gmail.com
# Modified for FreeBSD by Rene Ladan rene@freebsd.org

import os
import subprocess

FREEBSD_OS_NAME = 'freebsd'
PKG_ADD = 'pkg_add'

def register_installers(context):
    context.register_installer(PKG_ADD, PkgAddInstaller)
    
def register_cygwin(context):
    context.register_os_installer(FREEBSD_OS_NAME, 'source')
    context.register_os_installer(FREEBSD_OS_NAME, PKG_ADD)
    context.set_default_os_installer(FREEBSD_OS_NAME, PKG_ADD)

def cygcheck_detect(p):
    cmd = ['cygcheck', '-c', p]
    pop = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (std_out, std_err) = pop.communicate()
    return (std_out.count("OK") > 0)

def pkg_info_detect(p):
    if p == "builtin":
        return True
    # The next code is a lot of hassle, but there is no
    # better way in FreeBSD using just the base tools
    portname = p
    if p == "gtk20":
        portname = "gtk-2.\*"
    elif p == "py-gtk2":
        portname = "py27-gtk-2.\*"
    elif p[:9] in ["autoconf2", "automake1"]:
        portname = p[:8] + "-" + p[8] + "." + p[9:] + "\*"
    elif p[:3] == "py-":
        portname = "py27-" + p[3:] + "\*"
    else:
        portname = p + "-\*"
    pop = subprocess.Popen("/usr/sbin/pkg_info -qE " + portname, shell=True)
    return os.waitpid(pop.pid, 0)[1] == 0 # pkg_info -E returns 0 if pkg installed, 1 if not

class PkgAddInstaller(Installer):
    """
    An implementation of the Installer for use on freebsd-style
    systems.
    """

    def __init__(self, rosdep_rule_arg_dict):
        packages = rosdep_rule_arg_dict.get("packages", "")
        if type(packages) == type("string"):
            packages = packages.split()
        self.packages = packages

    def get_packages_to_install(self):
        return list(set(self.packages) - set(self.pkg_info_detect(self.packages)))

    def check_presence(self):
        return len(self.get_packages_to_install()) == 0

    def generate_package_install_command(self, default_yes = False, execute = True, display = True):
        if not packages:
            return "#No Packages to install"
        if default_yes:
            import sys
            print >> sys.stderr, "pkg_add does not have a default_yes option, continuing without"
        return "#Packages\nsudo /usr/sbin/pkg_add -r " + ' '.join(packages)
