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

from __future__ import print_function
import subprocess
import sys

from rospkg.os_detect import (
    OS_DEBIAN,
    OS_LINARO,
    OS_UBUNTU,
    OS_ELEMENTARY,
    OS_MX,
    OS_POP,
    OS_RASPBIAN,
    OS_ZORIN,
    OsDetect,
    read_os_release
)
from .pip import PIP_INSTALLER
from .gem import GEM_INSTALLER
from .npm import NPM_INSTALLER
from .source import SOURCE_INSTALLER
from ..installers import PackageManagerInstaller
from ..shell_utils import read_stdout

# apt package manager key
APT_INSTALLER = 'apt'


def register_installers(context):
    context.set_installer(APT_INSTALLER, AptInstaller())


def register_platforms(context):
    register_debian(context)
    register_ubuntu(context)

    # Aliases
    register_elementary(context)
    register_linaro(context)
    register_mx(context)
    register_pop(context)
    register_raspbian(context)
    register_zorin(context)


def register_debian(context):
    context.add_os_installer_key(OS_DEBIAN, APT_INSTALLER)
    context.add_os_installer_key(OS_DEBIAN, PIP_INSTALLER)
    context.add_os_installer_key(OS_DEBIAN, GEM_INSTALLER)
    context.add_os_installer_key(OS_DEBIAN, NPM_INSTALLER)
    context.add_os_installer_key(OS_DEBIAN, SOURCE_INSTALLER)
    context.set_default_os_installer_key(OS_DEBIAN, lambda self: APT_INSTALLER)
    context.set_os_version_type(OS_DEBIAN, OsDetect.get_codename)


def register_linaro(context):
    # Linaro is an alias for Ubuntu. If linaro is detected and it's not set as
    # an override force ubuntu.
    (os_name, os_version) = context.get_os_name_and_version()
    if os_name == OS_LINARO and not context.os_override:
        print('rosdep detected OS: [%s] aliasing it to: [%s]' %
              (OS_LINARO, OS_UBUNTU), file=sys.stderr)
        context.set_os_override(OS_UBUNTU, context.os_detect.get_codename())


def register_elementary(context):
    # Elementary is an alias for Ubuntu. If elementary is detected and it's
    # not set as an override force ubuntu.
    (os_name, os_version) = context.get_os_name_and_version()
    if os_name == OS_ELEMENTARY and not context.os_override:
        print('rosdep detected OS: [%s] aliasing it to: [%s]' %
              (OS_ELEMENTARY, OS_UBUNTU), file=sys.stderr)
        context.set_os_override(OS_UBUNTU, context.os_detect.get_codename())


def register_mx(context):
    # MX is an alias for Debian. If MX is detected and it's
    # not set as an override, force Debian.
    (os_name, os_version) = context.get_os_name_and_version()
    if os_name == OS_MX and not context.os_override:
        print('rosdep detected OS: [%s] aliasing it to: [%s]' %
              (OS_MX, OS_DEBIAN), file=sys.stderr)
        release_info = read_os_release()
        version = read_os_release()["VERSION"]
        context.set_os_override(OS_DEBIAN, version[version.find("(") + 1:version.find(")")])


def register_pop(context):
    # Pop! OS is an alias for Ubuntu. If Pop! is detected and it's
    # not set as an override force ubuntu.
    (os_name, os_version) = context.get_os_name_and_version()
    if os_name == OS_POP and not context.os_override:
        print('rosdep detected OS: [%s] aliasing it to: [%s]' %
              (OS_POP, OS_UBUNTU), file=sys.stderr)
        context.set_os_override(OS_UBUNTU, context.os_detect.get_codename())


def register_raspbian(context):
    # Raspbian is an alias for Debian. If Raspbian is detected and it's
    # not set as an override force Debian.
    (os_name, os_version) = context.get_os_name_and_version()
    if os_name == OS_RASPBIAN and not context.os_override:
        print('rosdep detected OS: [%s] aliasing it to: [%s]' %
              (OS_RASPBIAN, OS_DEBIAN), file=sys.stderr)
        context.set_os_override(OS_DEBIAN, context.os_detect.get_codename())


def register_zorin(context):
    # Zorin is an alias for Ubuntu. If Zorin is detected and it's
    # not set as an override force ubuntu.
    (os_name, os_version) = context.get_os_name_and_version()
    if os_name == OS_ZORIN and not context.os_override:
        print('rosdep detected OS: [%s] aliasing it to: [%s]' %
              (OS_ZORIN, OS_UBUNTU), file=sys.stderr)
        context.set_os_override(OS_UBUNTU, context.os_detect.get_codename())


def register_ubuntu(context):
    context.add_os_installer_key(OS_UBUNTU, APT_INSTALLER)
    context.add_os_installer_key(OS_UBUNTU, PIP_INSTALLER)
    context.add_os_installer_key(OS_UBUNTU, GEM_INSTALLER)
    context.add_os_installer_key(OS_UBUNTU, NPM_INSTALLER)
    context.add_os_installer_key(OS_UBUNTU, SOURCE_INSTALLER)
    context.set_default_os_installer_key(OS_UBUNTU, lambda self: APT_INSTALLER)
    context.set_os_version_type(OS_UBUNTU, OsDetect.get_codename)


def _read_apt_cache_showpkg(packages, exec_fn=None):
    """
    Output whether these packages are virtual package list providing package.
    If one package was not found, it gets returned as non-virtual.
    :param exec_fn: see `dpkg_detect`; make sure that exec_fn supports a
    second, boolean, parameter.
    """

    cmd = ['apt-cache', 'showpkg'] + packages
    if exec_fn is None:
        exec_fn = read_stdout

    std_out = exec_fn(cmd).splitlines()

    starts = []
    notfound = set()
    for p in packages:
        last_start = starts[-1] if len(starts) > 0 else 0
        try:
            starts.append(std_out.index('Package: %s' % p, last_start))
        except ValueError:
            notfound.add(p)
    starts.append(None)

    for p in packages:
        if p in notfound:
            yield p, False, None
            continue
        start = starts.pop(0)
        lines = iter(std_out[start:starts[0]])

        header = 'Package: %s' % p
        # proceed to Package header
        try:
            while next(lines) != header:
                pass
        except StopIteration:
            pass

        # proceed to versions section
        try:
            while next(lines) != 'Versions: ':
                pass
        except StopIteration:
            pass

        # virtual packages don't have versions
        try:
            if next(lines) != '':
                yield p, False, None
                continue
        except StopIteration:
            break

        # proceed to reserve provides section
        try:
            while next(lines) != 'Reverse Provides: ':
                pass
        except StopIteration:
            pass

        pr = [line.split(' ', 2)[0] for line in lines]
        if pr:
            yield p, True, pr
        else:
            yield p, False, None


def dpkg_detect(pkgs, exec_fn=None):
    """
    Given a list of package, return the list of installed packages.

    :param pkgs: list of package names, optionally followed by a fixed version (`foo=3.0`)
    :param exec_fn: function to execute Popen and read stdout (for testing)
    :return: list elements in *pkgs* that were found installed on the system
    """
    ret_list = []
    # this is mainly a hack to support version locking for eigen.
    # we strip version-locking syntax, e.g. libeigen3-dev=3.0.1-*.
    # our query does not do the validation on the version itself.
    # This is a map `package name -> package name optionally with version`.
    version_lock_map = {}
    for p in pkgs:
        if '=' in p:
            version_lock_map[p.split('=')[0]] = p
        else:
            version_lock_map[p] = p
    cmd = ['dpkg-query', '-W', '-f=\'${Package} ${Status}\n\'']
    cmd.extend(version_lock_map.keys())

    if exec_fn is None:
        exec_fn = read_stdout
    std_out, std_err = exec_fn(cmd, True)
    std_out = std_out.replace('\'', '')
    pkg_list = std_out.split('\n')
    for pkg in pkg_list:
        pkg_row = pkg.split()
        if len(pkg_row) == 4 and (pkg_row[3] == 'installed'):
            ret_list.append(pkg_row[0])
    installed_packages = [version_lock_map[r] for r in ret_list]

    # now for the remaining packages check, whether they are installed as
    # virtual packages
    remaining = _read_apt_cache_showpkg([p for p in pkgs if p not in installed_packages])
    virtual = [n for (n, v, pr) in remaining if v and len(dpkg_detect(pr)) > 0]

    return installed_packages + virtual


def _iterate_packages(packages, reinstall):
    for entry in _read_apt_cache_showpkg(packages):
        p, is_virtual, providers = entry
        if is_virtual:
            installed = []
            if reinstall:
                installed = dpkg_detect(providers)
                if len(installed) > 0:
                    for i in installed:
                        yield i
                    continue  # don't ouput providers
            yield providers
        else:
            yield p


class AptInstaller(PackageManagerInstaller):

    """
    An implementation of the Installer for use on debian style
    systems.
    """

    def __init__(self):
        super(AptInstaller, self).__init__(dpkg_detect)

    def get_version_strings(self):
        output = subprocess.check_output(['apt-get', '--version'])
        version = output.splitlines()[0].split(b' ')[1].decode()
        return ['apt-get {}'.format(version)]

    def _get_install_commands_for_package(self, base_cmd, package_or_list):
        def pkg_command(p):
            return self.elevate_priv(base_cmd + [p])

        if isinstance(package_or_list, list):
            return [pkg_command(p) for p in package_or_list]
        else:
            return pkg_command(package_or_list)

    def get_install_command(self, resolved, interactive=True, reinstall=False, quiet=False):
        packages = self.get_packages_to_install(resolved, reinstall=reinstall)
        if not packages:
            return []
        base_cmd = ['apt-get', 'install']
        if not interactive:
            base_cmd.append('-y')
        if quiet:
            base_cmd.append('-qq')

        return [self._get_install_commands_for_package(base_cmd, p) for p in _iterate_packages(packages, reinstall)]
