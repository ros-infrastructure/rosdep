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
import re
import sys

from rosdistro import get_cached_distribution, get_index, get_index_url
from rosdistro.dependency_walker import DependencyWalker, SourceDependencyWalker
from rosdistro.manifest_provider import get_release_tag


def get_distro(distro_name):
    index = get_index(get_index_url())
    return get_cached_distribution(index, distro_name)


def get_package_names(distro):
    released_names = []
    unreleased_names = []
    for pkg_name, pkg in distro.release_packages.items():
        repo = distro.repositories[pkg.repository_name].release_repository
        if repo:
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


def get_recursive_dependencies(distro, package_names, excludes=None, limit_depth=None, source=False):
    excludes = set(excludes or [])
    dependencies = set([])
    if source and distro.source_packages:
        walker = SourceDependencyWalker(distro)
    else:
        walker = DependencyWalker(distro)
    # redirect all stderr output to logger
    stderr = sys.stderr
    sys.stderr = CustomLogger()
    try:
        for pkg_name in package_names:
            try:
                dependencies |= walker.get_recursive_depends(pkg_name, ['buildtool', 'build', 'run', 'test'], ros_packages_only=True, ignore_pkgs=dependencies | excludes, limit_depth=limit_depth)
            except AssertionError as e:
                raise RuntimeError("Failed to fetch recursive dependencies of package '%s': %s" % (pkg_name, e))
    finally:
        sys.stderr = stderr
    dependencies -= set(package_names)
    return dependencies


def get_recursive_dependencies_on(distro, package_names, excludes=None, limit=None, source=False):
    excludes = set(excludes or [])
    limit = set(limit or [])
    dependencies = set([])
    if source and distro.source_packages:
        walker = SourceDependencyWalker(distro)
    else:
        walker = DependencyWalker(distro)

    # to improve performance limit search space if possible
    if limit:
        released_names, _ = get_package_names(distro)
        excludes.update(set(released_names) - limit - set(package_names))

    # redirect all stderr output to logger
    stderr = sys.stderr
    sys.stderr = CustomLogger()
    try:
        for pkg_name in package_names:
            dependencies |= walker.get_recursive_depends_on(pkg_name, ['buildtool', 'build', 'run', 'test'], ignore_pkgs=dependencies | excludes)
    finally:
        sys.stderr = stderr
    dependencies -= set(package_names)
    return dependencies


def generate_rosinstall(distro, package_names, flat=False, tar=False):
    rosinstall_data = []
    for pkg_name in package_names:
        rosinstall_data.extend(_generate_rosinstall_for_package(distro, pkg_name, flat=flat, tar=tar))
    return rosinstall_data


def _generate_rosinstall_for_package(distro, pkg_name, flat=False, tar=False):
    pkg = distro.release_packages[pkg_name]
    repo = distro.repositories[pkg.repository_name].release_repository
    assert repo is not None and repo.version is not None, 'Package "%s" does not have a version"' % pkg_name

    local_name = pkg_name
    if not flat and repo.package_names != [pkg_name]:
        local_name = '%s/%s' % (repo.name, local_name)
    release_tag = get_release_tag(repo, pkg_name)
    return _generate_rosinstall(local_name, repo.url, release_tag, tar=tar)


def _generate_rosinstall(local_name, url, release_tag, tar=False, vcs_type=None):
    logger = logging.getLogger('rosinstall_generator.generate')

    if tar:
        # Github tarball:    https://github.com/ros/ros_comm/archive/1.11.20.tar.gz
        # Bitbucket tarball: https://bitbucket.org/osrf/gazebo/get/gazebo7_7.3.1.tar.gz
        # Gitlab tarball:    https://gitlab.com/gitlab-org/gitlab-ce/repository/archive.tar.gz?ref=master
        match = re.match('(?:\w+:\/\/|git@)([\w.-]+)[:/]([\w/-]*)(?:\.git)?$', url)

        if match:
            server, repo_path = match.groups()
            url_templates = {
                'github': 'https://{0}/{1}/archive/{2}.tar.gz',
                'bitbucket': 'https://{0}/{1}/get/{2}.tar.gz',
                'gitlab': 'https://{0}/{1}/repository/archive.tar.gz?ref={2}'
            }
            for server_key, tarball_url_template in url_templates.items():
                if server_key in server:
                    return [{ 'tar': {
                        'local-name': local_name,
                        'uri': tarball_url_template.format(server, repo_path, release_tag),
                        'version': '{0}-{1}'.format(os.path.basename(repo_path), release_tag.replace('/', '-'))
                    }}]
            logger.log(logging.WARN, "Tarball requested for repo '{0}', but git server '{1}' is unrecognized.".format(
                local_name, server))
        else:
            logger.log(logging.WARN, "Tarball requested for repo '{0}', but I can't parse git URL '{1}'.".format(
                local_name, url))

        logger.log(logging.WARN, "Falling back on git clone for repo '{0}'.".format(local_name))

    return [{ vcs_type or 'git': {
        'local-name': local_name,
        'uri': url,
        'version': release_tag
    }}]
