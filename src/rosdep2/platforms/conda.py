# Copyright (c) 2021, Tobias Fischer
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

# Author Tobias Fischer/info@tobiasfischer.info
import subprocess
import json

from rospkg.os_detect import OS_CONDA

from ..installers import PackageManagerInstaller

CONDA_INSTALLER = 'conda'


def get_conda_mamba_cmd():
    candidate_list = ['micromamba', 'mamba', 'conda']
    for candidate in candidate_list:
        try:
            subprocess.Popen([candidate], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
            return candidate
        except OSError:
            continue
    raise Exception('None of ' + ', '.join(candidate_list) + ' was found.')


def register_installers(context):
    context.set_installer(CONDA_INSTALLER, CondaInstaller())


def register_platforms(context):
    context.add_os_installer_key(OS_CONDA, CONDA_INSTALLER)
    context.set_default_os_installer_key(OS_CONDA, lambda self: CONDA_INSTALLER)


def conda_detect(packages):
    conda_ret = json.loads(subprocess.check_output([get_conda_mamba_cmd(), 'list', '--json']))
    installed_package_names = [installed_package['name'] for installed_package in conda_ret]
    installed_package_versions = [installed_package['version'] for installed_package in conda_ret]
    ret_list = []
    for requested_package in packages:
        if requested_package == 'REQUIRE_OPENGL' or requested_package == 'REQUIRE_GL':
            ret_list.append(requested_package)
            continue

        if ' ' in requested_package:
            pkg_name = requested_package.split(' ')[0]
            pkg_version = requested_package.split(' ')[1]
            try:
                installed_package_idx = installed_package_names.index(pkg_name)
                if installed_package_versions[installed_package_idx] == pkg_version or installed_package_versions[installed_package_idx].startswith(pkg_version + '.'):
                    ret_list.append(requested_package)
            except ValueError:
                continue
        else:
            try:
                installed_package_idx = installed_package_names.index(requested_package)
                ret_list.append(requested_package)
            except ValueError:
                continue
    return ret_list


class CondaInstaller(PackageManagerInstaller):
    def __init__(self):
        super(CondaInstaller, self).__init__(conda_detect)

    def get_install_command(self, resolved, interactive=True, reinstall=False, quiet=False):
        packages = self.get_packages_to_install(resolved, reinstall=reinstall)
        packages = [p if ' ' not in p else p.replace(' ', '=') for p in packages]

        if not packages:
            return []

        base_cmd = [get_conda_mamba_cmd(), 'install']

        channels = ['robostack', 'conda-forge']
        for channel in channels:
            base_cmd += ['-c', channel]

        if not interactive:
            base_cmd.append('-y')
        if quiet:
            base_cmd.append('-q')
        if reinstall:
            base_cmd.append('--force-reinstall')

        return [base_cmd + packages]

    def get_version_strings(self):
        return subprocess.check_output((get_conda_mamba_cmd(), '--version'))
