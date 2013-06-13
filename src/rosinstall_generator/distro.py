import yaml

from rosdistro import get_cached_release, get_index, get_index_url, RosDistro
from rosdistro.dependency_walker import DependencyWalker
from rosdistro.manifest_provider import get_release_tag
from rospkg.distro import distro_uri, load_distro

import logging
logger = logging.getLogger('submit_jobs')


def logger_print(msg, end='', file=None):
    end = '' if end is None else end
    logger.info(msg + str(end))

import rosdistro.common
rosdistro.common.override_print(logger_print)


#Generates a rosinstall file for a package and it's dependences
def generate_rosinstall(distro_name, packages, check_variants=True):
    if distro_name != 'fuerte':
        return _generate_rosinstall(distro_name, packages, check_variants)
    else:
        return _generate_rosinstall_fuerte(distro_name, packages, check_variants)


def _generate_rosinstall(distro_name, packages, check_variants=True):
    packages = packages if type(packages) == list else [packages]
    index = get_index(get_index_url())
    dist = get_cached_release(index, distro_name)
    dry_distro = load_distro(distro_uri(distro_name))

    #First, we want to check if there is a dry variant that has been requested
    if check_variants and len(packages) == 1 and packages[0] in dry_distro.variants:
        logger.info("Found variant %s" % packages[0])
        all_packages = dry_distro.variants[packages[0]].get_stack_names()
        packages = list(set([p for p in all_packages if p in dist.packages.keys()]))
        logger.info("Building rosinstall for wet packages: %s" % packages)

    walker = DependencyWalker(dist)
    all_pkgs = set([])
    for pkg_name in packages:
        assert pkg_name in dist.packages, 'Package "%s" is not part of distro "%s"' % (pkg_name, distro_name)
        all_pkgs |= walker.get_recursive_depends(pkg_name, ['buildtool', 'build', 'run'], ros_packages_only=True, ignore_pkgs=all_pkgs)
    all_pkgs |= set(packages)

    rosinstalls = []
    for pkg_name in all_pkgs:
        rosinstalls.append(_generate_rosinstall_for_package(dist, pkg_name))

    return '\n'.join(rosinstalls)


def _generate_rosinstall_for_package(dist, pkg_name):
    pkg = dist.packages[pkg_name]
    repo = dist.repositories[pkg.repository_name]
    assert repo.version is not None, 'Package "%s" does not have a version" % pkg_name'

    url = repo.url
    release_tag = get_release_tag(repo, pkg_name)
    url = url.replace('.git', '/archive/{0}.tar.gz'.format(release_tag))
    return yaml.safe_dump([{
        'tar': {
            'local-name': pkg_name,
            'uri': url,
            'version': '{0}-release-{1}'.format(repo.name, release_tag.replace('/', '-'))
        }}],
        default_style=False)


def _generate_rosinstall_fuerte(distro_name, packages, check_variants=True):
    packages = packages if type(packages) == list else [packages]
    distro = RosDistro(distro_name)
    dry_distro = load_distro(distro_uri(distro_name))

    #First, we want to check if there is a dry variant that has been requested
    if check_variants and len(packages) == 1 and packages[0] in dry_distro.variants:
        logger.info("Found variant %s" % packages[0])
        all_packages = dry_distro.variants[packages[0]].get_stack_names()
        packages = list(set([p for p in all_packages if p in distro.get_packages()]))
        logger.info("Building rosinstall for wet packages: %s" % packages)

    deps = distro.get_depends(packages)
    deps = list(set(deps['build'] + deps['run'] + deps['buildtool']))
    distro_pkgs = [p for p in list(set(deps + packages)) if p in distro.get_packages()]

    rosinstall = distro.get_rosinstall(distro_pkgs, source='tar')

    return rosinstall
