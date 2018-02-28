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

from __future__ import print_function

import copy
import logging
import os

from catkin_pkg.package import InvalidPackage, parse_package_string
from catkin_pkg.packages import find_packages_allowing_duplicates

from rospkg import RosPack, RosStack
from rospkg.environment import ROS_PACKAGE_PATH

from rosinstall_generator.distro import get_distro as _get_wet_distro
from rosinstall_generator.distro import generate_rosinstall as generate_wet_rosinstall
from rosinstall_generator.distro import get_recursive_dependencies as get_recursive_dependencies_of_wet
from rosinstall_generator.distro import get_recursive_dependencies_on as get_recursive_dependencies_on_of_wet
from rosinstall_generator.distro import get_package_names
from rosinstall_generator.distro import _generate_rosinstall

from rosinstall_generator.dry_distro import get_distro as _get_dry_distro
from rosinstall_generator.dry_distro import generate_rosinstall as generate_dry_rosinstall
from rosinstall_generator.dry_distro import get_recursive_dependencies as get_recursive_dependencies_of_dry
from rosinstall_generator.dry_distro import get_recursive_dependencies_on as get_recursive_dependencies_on_of_dry
from rosinstall_generator.dry_distro import get_stack_names

logger = logging.getLogger('rosinstall_generator')

ARG_ALL_PACKAGES = 'ALL'
ARG_CURRENT_ENVIRONMENT = 'RPP'


def _split_special_keywords(names):
    non_keyword_names = set(names)
    keywords = set([])
    if ARG_ALL_PACKAGES in names:
        non_keyword_names.remove(ARG_ALL_PACKAGES)
        keywords.add(ARG_ALL_PACKAGES)
    if ARG_CURRENT_ENVIRONMENT in names:
        non_keyword_names.remove(ARG_CURRENT_ENVIRONMENT)
        keywords.add(ARG_CURRENT_ENVIRONMENT)
    return non_keyword_names, keywords


def _classify_repo_names(distro_name, repo_names):
    names = set([])
    unknown_names = set([])
    if repo_names:
        wet_distro = get_wet_distro(distro_name)
        for repo_name in repo_names:
            if repo_name in wet_distro.repositories:
                names.add(repo_name)
            else:
                unknown_names.add(repo_name)
    return names, unknown_names


def _get_packages_for_repos(distro_name, repo_names, source=False):
    package_names = set([])
    unreleased_repo_names = set([])
    wet_distro = get_wet_distro(distro_name)
    for repo_name in repo_names:
        if source:
            # Returns a mapping of package names to package XML strings in particular repo.
            source_package_xmls = wet_distro.get_source_repo_package_xmls(repo_name)
        if source and source_package_xmls:
            package_names.update(source_package_xmls.keys())
        else:
            release_repo = wet_distro.repositories[repo_name].release_repository
            if release_repo:
                package_names.update(release_repo.package_names)
            else:
                unreleased_repo_names.add(repo_name)
    return package_names, unreleased_repo_names


def _classify_names(distro_name, names, source=False):
    unknown_names = set(names or [])

    wet_package_names = set([])
    dry_stack_names = set([])
    variant_names = set([])

    # identify wet packages
    if unknown_names:
        wet_distro = get_wet_distro(distro_name)
        packages = wet_distro.source_packages if source and wet_distro.source_packages else wet_distro.release_packages
        for name in unknown_names:
            if name in packages:
                wet_package_names.add(name)
        unknown_names -= wet_package_names

    if distro_name == 'groovy':
        # identify dry stacks/variants
        if unknown_names:
            dry_distro = get_dry_distro(distro_name)
            for name in unknown_names:
                if name in dry_distro.get_stacks(released=True):
                    dry_stack_names.add(name)
                if name in dry_distro.variants:
                    variant_names.add(name)
            unknown_names -= dry_stack_names
            unknown_names -= variant_names

        # resolve variant names into wet package names or dry stack names
        if variant_names:
            wet_distro = get_wet_distro(distro_name)
            for variant_name in variant_names:
                variant_depends = dry_distro.variants[variant_name].get_stack_names()
                for depend in variant_depends:
                    if depend in wet_distro.release_packages:
                        wet_package_names.add(depend)
                    elif depend in dry_distro.stacks:
                        dry_stack_names.add(depend)
                    else:
                        raise RuntimeError("The following dependency of variant '%s' could not be found: %s" % (variant_name, depend))

    return Names(wet_package_names, dry_stack_names), unknown_names


def generate_rosinstall_for_repos(repos, version_tag=True, tar=False):
    rosinstall_data = []
    for repo in repos.values():
        if version_tag:
            version = repo.release_repository.version.split('-')[0]
            vcs_type = repo.release_repository.type
        else:
            version = repo.source_repository.version
            vcs_type = repo.source_repository.type
        rosinstall_data += _generate_rosinstall(repo.name, repo.source_repository.url, version, tar=tar, vcs_type=vcs_type)
    return rosinstall_data


class Names(object):
    '''
    Stores wet package names and dry stack names.
    '''

    def __init__(self, wet_package_names, dry_stack_names):
        self.wet_package_names = set(wet_package_names)
        self.dry_stack_names = set(dry_stack_names)

    def update(self, other):
        self.wet_package_names.update(other.wet_package_names)
        self.dry_stack_names.update(other.dry_stack_names)


def _expand_keywords(distro_name, keywords):
    names = set([])
    if ARG_ALL_PACKAGES in keywords:
        wet_distro = get_wet_distro(distro_name)
        released_package_names, _ = get_package_names(wet_distro)
        names.update(released_package_names)
        if distro_name == 'groovy':
            dry_distro = get_dry_distro(distro_name)
            released_stack_names, _ = get_stack_names(dry_distro)
            names.update(released_stack_names)
    if ARG_CURRENT_ENVIRONMENT in keywords:
        names.update(_get_packages_in_environment())
    return names


_packages_in_environment = None


def _get_packages_in_environment():
    global _packages_in_environment
    if _packages_in_environment is None:
        if ROS_PACKAGE_PATH not in os.environ or not os.environ[ROS_PACKAGE_PATH]:
            raise RuntimeError("The environment variable '%s' must be set when using '%s'" % (ROS_PACKAGE_PATH, ARG_CURRENT_ENVIRONMENT))
        _packages_in_environment = set([])
        rs = RosStack()
        _packages_in_environment.update(set(rs.list()))
        rp = RosPack()
        _packages_in_environment.update(set(rp.list()))
    return _packages_in_environment


def _get_package_names(path):
    return set([pkg.name for _, pkg in find_packages_allowing_duplicates(path).items()])


_wet_distro = None
_dry_distro = None


def get_wet_distro(distro_name):
    global _wet_distro
    if _wet_distro is None:
        _wet_distro = _get_wet_distro(distro_name)
    return _wet_distro


def get_dry_distro(distro_name):
    global _dry_distro
    if _dry_distro is None and distro_name == 'groovy':
        _dry_distro = _get_dry_distro(distro_name)
    return _dry_distro


def generate_rosinstall(distro_name, names,
    from_paths=None, repo_names=None,
    deps=False, deps_up_to=None, deps_depth=None, deps_only=False,
    wet_only=False, dry_only=False, catkin_only=False, non_catkin_only=False,
    excludes=None, exclude_paths=None,
    flat=False,
    tar=False,
    upstream_version_tag=False, upstream_source_version=False):

    # classify package/stack names
    names, keywords = _split_special_keywords(names)

    # find packages recursively in include paths
    if from_paths:
        include_names_from_path = set([])
        [include_names_from_path.update(_get_package_names(from_path)) for from_path in from_paths]
        logger.debug("The following wet packages found in '--from-path' will be considered: %s" % ', '.join(sorted(include_names_from_path)))
        names.update(include_names_from_path)

    # expand repository names into package names
    repo_names, unknown_repo_names = _classify_repo_names(distro_name, repo_names)
    if unknown_repo_names:
        logger.warn('The following unknown repositories will be ignored: %s' % (', '.join(sorted(unknown_repo_names))))
    wet_package_names, unreleased_repo_names = _get_packages_for_repos(distro_name, repo_names, source=upstream_source_version)
    names.update(wet_package_names)
    if unreleased_repo_names and not upstream_version_tag and not upstream_source_version:
        logger.warn('The following unreleased repositories will be ignored: %s' % ', '.join(sorted(unreleased_repo_names)))
    if unreleased_repo_names and (deps or deps_up_to) and (upstream_version_tag or upstream_source_version):
        logger.warn('The dependencies of the following unreleased repositories are unknown and will be ignored: %s' % ', '.join(sorted(unreleased_repo_names)))
    has_repos = ((repo_names - unreleased_repo_names) and (upstream_version_tag or upstream_source_version)) or (unreleased_repo_names and upstream_source_version)

    names, unknown_names = _classify_names(distro_name, names, source=upstream_source_version)
    if unknown_names:
        logger.warn('The following not released packages/stacks will be ignored: %s' % (', '.join(sorted(unknown_names))))
    if keywords:
        expanded_names, unknown_names = _classify_names(distro_name, _expand_keywords(distro_name, keywords), source=upstream_source_version)
        if unknown_names:
            logger.warn('The following not released packages/stacks from the %s will be ignored: %s' % (ROS_PACKAGE_PATH, ', '.join(sorted(unknown_names))))
        names.update(expanded_names)
    if not names.wet_package_names and not names.dry_stack_names and not has_repos:
        raise RuntimeError('No packages/stacks left after ignoring not released')
    if names.wet_package_names or names.dry_stack_names:
        logger.debug('Packages/stacks: %s' % ', '.join(sorted(names.wet_package_names | names.dry_stack_names)))
    if unreleased_repo_names:
        logger.debug('Unreleased repositories: %s' % ', '.join(sorted(unreleased_repo_names)))

    # classify deps-up-to
    deps_up_to_names, keywords = _split_special_keywords(deps_up_to or [])
    deps_up_to_names, unknown_names = _classify_names(distro_name, deps_up_to_names, source=upstream_source_version)
    if unknown_names:
        logger.warn("The following not released '--deps-up-to' packages/stacks will be ignored: %s" % (', '.join(sorted(unknown_names))))
    if keywords:
        expanded_names, unknown_names = _classify_names(distro_name, _expand_keywords(distro_name, keywords), source=upstream_source_version)
        if unknown_names:
            logger.warn("The following not released '--deps-up-to' packages/stacks from the %s will be ignored: %s" % (ROS_PACKAGE_PATH, ', '.join(sorted(unknown_names))))
        deps_up_to_names.update(expanded_names)
    if deps_up_to:
        logger.debug('Dependencies up to: %s' % ', '.join(sorted(deps_up_to_names.wet_package_names | deps_up_to_names.dry_stack_names)))

    # classify excludes
    exclude_names, keywords = _split_special_keywords(excludes or [])
    if exclude_paths:
        exclude_names_from_path = set([])
        [exclude_names_from_path.update(_get_package_names(exclude_path)) for exclude_path in exclude_paths]
        logger.debug("The following wet packages found in '--exclude-path' will be excluded: %s" % ', '.join(sorted(exclude_names_from_path)))
        exclude_names.update(exclude_names_from_path)
    exclude_names, unknown_names = _classify_names(distro_name, exclude_names, source=upstream_source_version)
    if unknown_names:
        logger.warn("The following not released '--exclude' packages/stacks will be ignored: %s" % (', '.join(sorted(unknown_names))))
    if keywords:
        expanded_names, unknown_names = _classify_names(distro_name, _expand_keywords(distro_name, keywords), source=upstream_source_version)
        exclude_names.update(expanded_names)
    if excludes:
        logger.debug('Excluded packages/stacks: %s' % ', '.join(sorted(exclude_names.wet_package_names | exclude_names.dry_stack_names)))

    result = copy.deepcopy(names)
    # clear wet packages if not requested
    if dry_only:
        result.wet_package_names.clear()
    # clear dry packages if not requested and no dependencies
    if wet_only and not deps and not deps_up_to:
        result.dry_stack_names.clear()

    # remove excluded names from the list of wet and dry names
    result.wet_package_names -= exclude_names.wet_package_names
    result.dry_stack_names -= exclude_names.dry_stack_names
    if not result.wet_package_names and not result.dry_stack_names and not has_repos:
        raise RuntimeError('No packages/stacks left after applying the exclusions')

    if result.wet_package_names:
        logger.debug('Wet packages: %s' % ', '.join(sorted(result.wet_package_names)))
    if result.dry_stack_names:
        logger.debug('Dry stacks: %s' % ', '.join(sorted(result.dry_stack_names)))

    # extend the names with recursive dependencies
    if deps or deps_up_to:
        # add dry dependencies
        if result.dry_stack_names:
            dry_distro = get_dry_distro(distro_name)
            _, unreleased_stack_names = get_stack_names(dry_distro)
            excludes = exclude_names.dry_stack_names | deps_up_to_names.dry_stack_names | set(unreleased_stack_names)
            dry_dependencies, wet_dependencies = get_recursive_dependencies_of_dry(dry_distro, result.dry_stack_names, excludes=excludes)
            logger.debug('Dry stacks including dependencies: %s' % ', '.join(sorted(dry_dependencies)))
            result.dry_stack_names |= dry_dependencies

            if not dry_only:
                # add wet dependencies of dry stuff
                logger.debug('Wet dependencies of dry stacks: %s' % ', '.join(sorted(wet_dependencies)))
                for depend in wet_dependencies:
                    if depend in exclude_names.wet_package_names or depend in deps_up_to_names.wet_package_names:
                        continue
                    wet_distro = get_wet_distro(distro_name)
                    assert depend in wet_distro.release_packages, "Package '%s' does not have a version" % depend
                    result.wet_package_names.add(depend)
        # add wet dependencies
        if result.wet_package_names:
            wet_distro = get_wet_distro(distro_name)
            _, unreleased_package_names = get_package_names(wet_distro)
            excludes = exclude_names.wet_package_names | deps_up_to_names.wet_package_names | set(unreleased_package_names)
            result.wet_package_names |= get_recursive_dependencies_of_wet(wet_distro, result.wet_package_names, excludes=excludes,
                    limit_depth=deps_depth, source=upstream_source_version)
            logger.debug('Wet packages including dependencies: %s' % ', '.join(sorted(result.wet_package_names)))

    # intersect result with recursive dependencies on
    if deps_up_to:
        # intersect with wet dependencies on
        if deps_up_to_names.wet_package_names:
            wet_distro = get_wet_distro(distro_name)
            # wet depends on do not include the names since they are excluded to stop recursion asap
            wet_package_names = get_recursive_dependencies_on_of_wet(wet_distro, deps_up_to_names.wet_package_names, excludes=names.wet_package_names,
                    limit=result.wet_package_names, source=upstream_source_version)
            # keep all names which are already in the result set
            wet_package_names |= result.wet_package_names & names.wet_package_names
            result.wet_package_names = wet_package_names
        else:
            result.wet_package_names.clear()
        logger.debug('Wet packages after intersection: %s' % ', '.join(sorted(result.wet_package_names)))

        # intersect with dry dependencies on
        dry_dependency_names = result.wet_package_names | deps_up_to_names.dry_stack_names
        if dry_dependency_names and not wet_only:
            dry_distro = get_dry_distro(distro_name)
            # dry depends on do not include the names since they are excluded to stop recursion asap
            dry_stack_names = get_recursive_dependencies_on_of_dry(dry_distro, dry_dependency_names, excludes=names.dry_stack_names, limit=result.dry_stack_names)
            # keep all names which are already in the result set
            dry_stack_names |= result.dry_stack_names & names.dry_stack_names
            result.dry_stack_names = dry_stack_names
        else:
            result.dry_stack_names.clear()
        logger.debug('Dry stacks after intersection: %s' % ', '.join(sorted(result.dry_stack_names)))

    # exclude passed in names
    if deps_only:
        result.wet_package_names -= set(names.wet_package_names)
        result.dry_stack_names -= set(names.dry_stack_names)

    # exclude wet packages based on build type
    if catkin_only or non_catkin_only:
        wet_distro = get_wet_distro(distro_name)
        for pkg_name in list(result.wet_package_names):
            pkg_xml = wet_distro.get_release_package_xml(pkg_name)
            try:
                pkg = parse_package_string(pkg_xml)
            except InvalidPackage as e:
                logger.warn("The package '%s' has an invalid manifest and will be ignored: %s" % (pkg_name, e))
                result.wet_package_names.remove(pkg_name)
                continue
            build_type = ([e.content for e in pkg.exports if e.tagname == 'build_type'][0]) if 'build_type' in [e.tagname for e in pkg.exports] else 'catkin'
            if catkin_only ^ (build_type == 'catkin'):
                result.wet_package_names.remove(pkg_name)

    # get wet and/or dry rosinstall data
    rosinstall_data = []
    if not dry_only and (result.wet_package_names or has_repos):
        wet_distro = get_wet_distro(distro_name)
        if upstream_version_tag or upstream_source_version:
            # determine repositories based on package names and passed in repository names
            repos = {}
            for pkg_name in result.wet_package_names:
                if upstream_source_version and wet_distro.source_packages:
                    pkg = wet_distro.source_packages[pkg_name]
                    repos[pkg.repository_name] = wet_distro.repositories[pkg.repository_name]
                else:
                    pkg = wet_distro.release_packages[pkg_name]
                    if pkg.repository_name not in repos:
                        repo = wet_distro.repositories[pkg.repository_name]
                        release_repo = repo.release_repository
                        assert not upstream_version_tag or release_repo.version is not None, "Package '%s' in repository '%s' does not have a release version" % (pkg_name, pkg.repository_name)
                        repos[pkg.repository_name] = repo
            for repo_name in repo_names:
                if repo_name not in repos:
                    repos[repo_name] = wet_distro.repositories[repo_name]
            # ignore repos which lack information
            repos_without_source = [repo_name for repo_name, repo in repos.items() if not repo.source_repository]
            if repos_without_source:
                logger.warn('The following repositories with an unknown upstream will be ignored: %s' % ', '.join(sorted(repos_without_source)))
                [repos.pop(repo_name) for repo_name in repos_without_source]
            if upstream_version_tag:
                repos_without_release = [repo_name for repo_name, repo in repos.items() if not repo.release_repository or not repo.release_repository.version]
                if repos_without_release:
                    logger.warn('The following repositories without a release will be ignored: %s' % ', '.join(sorted(repos_without_release)))
                    [repos.pop(repo_name) for repo_name in repos_without_release]
            logger.debug('Generate rosinstall entries for wet repositories: %s' % ', '.join(sorted(repos.keys())))
            wet_rosinstall_data = generate_rosinstall_for_repos(repos, version_tag=upstream_version_tag, tar=tar)
            rosinstall_data += wet_rosinstall_data
        else:
            logger.debug('Generate rosinstall entries for wet packages: %s' % ', '.join(sorted(result.wet_package_names)))
            wet_rosinstall_data = generate_wet_rosinstall(wet_distro, result.wet_package_names, flat=flat, tar=tar)
            rosinstall_data += wet_rosinstall_data
    if not wet_only and result.dry_stack_names:
        logger.debug('Generate rosinstall entries for dry stacks: %s' % ', '.join(sorted(result.dry_stack_names)))
        dry_distro = get_dry_distro(distro_name)
        dry_rosinstall_data = generate_dry_rosinstall(dry_distro, result.dry_stack_names)
        rosinstall_data += dry_rosinstall_data
    return rosinstall_data


def sort_rosinstall(rosinstall_data):
    def _rosinstall_key(item):
        key = list(item.keys())[0]
        return item[key]['local-name']
    return sorted(rosinstall_data, key=_rosinstall_key)
