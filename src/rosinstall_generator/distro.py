# Software License Agreement (BSD License)
#
# Copyright (c) 2013, Open Source Robotics Foundation, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above
#    copyright notice, this list of conditions and the following
#    disclaimer in the documentation and/or other materials provided
#    with the distribution.
#  * Neither the name of Open Source Robotics Foundation, Inc. nor
#    the names of its contributors may be used to endorse or promote
#    products derived from this software without specific prior
#    written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import logging
import os
import sys

from rosdistro import get_cached_release, get_index, get_index_url
from rosdistro.dependency_walker import DependencyWalker
from rosdistro.manifest_provider import get_release_tag


def get_distro(distro_name):
    index = get_index(get_index_url())
    return get_cached_release(index, distro_name)


def get_package_names(distro):
    released_names = []
    unreleased_names = []
    for pkg_name, pkg in distro.packages.items():
        repo = distro.repositories[pkg.repository_name]
        if repo.version is not None:
            released_names.append(pkg_name)
        else:
            unreleased_names.append(pkg_name)
    return released_names, unreleased_names


# redirect all output to logger
class CustomLogger(object):

    def __init__(self):
        self.logger = logging.getLogger('rosinstall_generator.wet')
        self.linebuf = ''

    def write(self, buf):
      for line in buf.rstrip().splitlines():
         self.logger.log(logging.DEBUG, line.rstrip())


def get_recursive_dependencies(distro, package_names, excludes=None):
    excludes = set(excludes or [])
    dependencies = set([])
    walker = DependencyWalker(distro)
    # redirect all stderr output to logger
    stderr = sys.stderr
    sys.stderr = CustomLogger()
    try:
        for pkg_name in package_names:
            try:
                dependencies |= walker.get_recursive_depends(pkg_name, ['buildtool', 'build', 'run'], ros_packages_only=True, ignore_pkgs=dependencies | excludes)
            except AssertionError as e:
                raise RuntimeError("Failed to fetch recursive dependencies of package '%s': %s" % (pkg_name, e))
    finally:
        sys.stderr = stderr
    dependencies -= set(package_names)
    return dependencies


def get_recursive_dependencies_on(distro, package_names, excludes=None, limit=None):
    excludes = set(excludes or [])
    limit = set(limit or [])

    # to improve performance limit search space if possible
    if limit:
        released_names, _ = get_package_names(distro)
        excludes.update(set(released_names) - limit - set(package_names))

    dependencies = set([])
    walker = DependencyWalker(distro)
    # redirect all stderr output to logger
    stderr = sys.stderr
    sys.stderr = CustomLogger()
    try:
        for pkg_name in package_names:
            dependencies |= walker.get_recursive_depends_on(pkg_name, ['buildtool', 'build', 'run'], ignore_pkgs=dependencies | excludes)
    finally:
        sys.stderr = stderr
    dependencies -= set(package_names)
    return dependencies


def generate_rosinstall(distro, package_names, tar=False):
    rosinstall_data = []
    for pkg_name in package_names:
        rosinstall_data.extend(_generate_rosinstall_for_package(distro, pkg_name, tar=tar))
    return rosinstall_data


def _generate_rosinstall_for_package(distro, pkg_name, tar):
    pkg = distro.packages[pkg_name]
    repo = distro.repositories[pkg.repository_name]
    assert repo.version is not None, 'Package "%s" does not have a version"' % pkg_name

    url = repo.url
    release_tag = get_release_tag(repo, pkg_name)
    if tar:
        # the repository name might be different than repo.name coming from rosdistro
        repo_name = os.path.basename(url[:-4])
        url = url.replace('.git', '/archive/{0}.tar.gz'.format(release_tag))
        data = [{
            'tar': {
                'local-name': pkg_name,
                'uri': url,
                'version': '{0}-{1}'.format(repo_name, release_tag.replace('/', '-'))
            }
        }]
    else:
        data = [{
            'git': {
                'local-name': pkg_name,
                'uri': url,
                'version': release_tag
            }
        }]
    return data
