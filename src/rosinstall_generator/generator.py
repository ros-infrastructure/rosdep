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

from rosinstall_generator.distro import get_distro as get_wet_distro
from rosinstall_generator.distro import generate_rosinstall as generate_wet_rosinstall
from rosinstall_generator.distro import get_recursive_dependencies as get_recursive_dependencies_of_wet

from rosinstall_generator.dry_distro import get_distro as get_dry_distro
from rosinstall_generator.dry_distro import generate_rosinstall as generate_dry_rosinstall
from rosinstall_generator.dry_distro import get_recursive_dependencies as get_recursive_dependencies_of_dry

logger = logging.getLogger('rosinstall_generator')


def generate_rosinstall(distro_name, names, wet_only=False, dry_only=False, deps=False, tar=False):
    unknown_names = set(names)
    wet_package_names = set([])
    dry_names = set([])

    # identify wet packages
    wet_distro = get_wet_distro(distro_name)
    for pkg_name in unknown_names:
        if pkg_name in wet_distro.packages:
            wet_package_names.add(pkg_name)
    unknown_names -= wet_package_names

    # identify dry stacks/variants if necessary
    if unknown_names:
        dry_distro = get_dry_distro(distro_name)
        for pkg_name in unknown_names:
            if pkg_name in dry_distro.get_stacks(released=True) or pkg_name in dry_distro.variants:
                dry_names.add(pkg_name)
        unknown_names -= dry_names

    if unknown_names:
        raise RuntimeError('The following packages could not be found: ' + ', '.join(sorted(unknown_names)))

    # clear wet packages if not requested
    if dry_only and wet_package_names:
        wet_package_names.clear()

    # clear dry packages if not requested and no dependencies
    if wet_only and not deps and dry_names:
        dry_names.clear()

    if wet_package_names:
        logger.debug('wet_package_names: %s' % ', '.join(sorted(wet_package_names)))
    if dry_names:
        logger.debug('dry_names: %s' % ', '.join(sorted(dry_names)))

    # replace variant names with wet package names or dry stack names
    dry_stack_names = set([])
    for dry_name in dry_names:
        if dry_name in dry_distro.variants:
            variant_depends = dry_distro.variants[dry_name].get_stack_names()
            for depend in variant_depends:
                if depend in wet_distro.packages:
                    wet_package_names.add(depend)
                elif depend in dry_distro.stacks:
                    dry_stack_names.add(depend)
                else:
                    raise RuntimeError('The following dependency of variant "%s" could not be found: %s' % (dry_name, depend))
        else:
            dry_stack_names.add(dry_name)
    if dry_stack_names:
        logger.debug('dry_stack_names: %s' % ', '.join(sorted(dry_stack_names)))

    # extend the names with recursive dependencies
    if deps:
        # add dry dependencies
        if dry_stack_names:
            dry_dependencies, wet_dependencies = get_recursive_dependencies_of_dry(dry_distro, dry_stack_names)
            logger.debug('dry_dependencies: %s' % ', '.join(sorted(dry_dependencies)))
            dry_stack_names |= dry_dependencies

            if not dry_only:
                # add wet dependencies of dry stuff
                logger.debug('wet_dependencies: %s' % ', '.join(sorted(wet_dependencies)))
                for depend in wet_dependencies:
                    assert depend in wet_distro.packages, 'Package "%s" does not have a version"' % depend
                    wet_package_names.add(depend)
        # add wet dependencies
        if wet_package_names:
            wet_package_names = get_recursive_dependencies_of_wet(wet_distro, wet_package_names)
            logger.debug('wet_package_names: %s' % ', '.join(sorted(wet_package_names)))

    rosinstall_data = []
    if not dry_only and wet_package_names:
        wet_rosinstall_data = generate_wet_rosinstall(wet_distro, wet_package_names, tar=tar)
        rosinstall_data += wet_rosinstall_data
    if not wet_only and dry_stack_names:
        dry_rosinstall_data = generate_dry_rosinstall(dry_distro, dry_stack_names)
        rosinstall_data += dry_rosinstall_data
    return rosinstall_data


def sort_rosinstall(rosinstall_data):
    def _rosinstall_compare(a, b):
        a_key = a.keys()[0]
        b_key = b.keys()[0]
        a_name = a[a_key]['local-name']
        b_name = b[b_key]['local-name']
        if a_name < b_name:
            return -1
        if a_name > b_name:
            return 1
        return 0
    return sorted(rosinstall_data, _rosinstall_compare)
