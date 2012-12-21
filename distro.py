import urllib2
import sys
import yaml
import time
from Queue import Queue
from threading import Thread
from rosdistro import RosDistro
from rospkg.distro import load_distro, distro_uri

import logging
logger = logging.getLogger('submit_jobs')

#Generates a rosinstall file for a package and it's dependences
def generate_rosinstall(distro_name, packages, check_variants=True):
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
