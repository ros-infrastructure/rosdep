from __future__ import print_function
from setuptools import setup
# setuptools overrides sdist and build_py
from setuptools.command.build_py import build_py
from setuptools.command.sdist import sdist

# setuptools does not override clean
from distutils.command.clean import clean

import sys
import os
import shutil
sys.path.insert(0, 'src')

from rosdep2 import __version__
from rosdep2.sources_list import get_default_prefix

install_prefix = get_default_prefix()

cache_dir = os.path.join('src','rosdep2','cache')

def create_cache():
    """ Build the cache for distribution.
    This only builds the cache if it doesn't exist """
    # only build the cache if it doesn't exist
    if not os.path.isdir(cache_dir) or len(os.listdir(cache_dir)) == 0:
        print("building cache into", cache_dir)
        from rosdep2.sources_list import update_sources_list, DEFAULT_SOURCES_LIST
        update_sources_list(sources_files=[DEFAULT_SOURCES_LIST], sources_cache_dir=cache_dir)

def get_cache_files():
    """ Get the listing of files that are part of the cache.
    This MUST be called after the cache exists """
    return [os.path.join(cache_dir, f) for f in os.listdir(cache_dir)]


class rosdep_build(build_py):
    def finalize_options(self):
        create_cache()
        build_py.finalize_options(self)
        print("build_py data files", self.data_files)
        print("build_py package data", self.package_data)
        print("distribution data_files", self.distribution.data_files)
        cache_files = get_cache_files()
        if not self.distribution.has_data_files():
            self.distribution.data_files = []
        self.distribution.data_files.append(
            (os.path.join(install_prefix, 'var/cache/rosdep'), cache_files))
        self.package_data['rosdep2.cache'] = os.listdir(cache_dir)
        # format: package, source dir, build dir, files
        self.data_files.append((
            'rosdep2.cache',
            cache_dir,
            os.path.join('build','lib','rosdep2','cache'),
            os.listdir(cache_dir)))
        print("build_py data files", self.data_files)
        print("build_py package data", self.package_data)
        print("distribution data_files", self.distribution.data_files)
        print("Finalized build_py")

class rosdep_clean(clean):
    def run(self):
        # remove the built cache
        # this is the reverse of create_cache
        if os.path.isdir(cache_dir):
            shutil.rmtree(cache_dir)
        clean.run(self)

class rosdep_sdist(sdist):
    def run(self):
        create_cache()
        sdist.run(self)


cmdclass = { 'build_py': rosdep_build, 
             'clean': rosdep_clean,
             'sdist': rosdep_sdist,
             }

setup(
    name='rosdep',
    version=__version__,
    cmdclass=cmdclass,
    packages=['rosdep2', 'rosdep2.platforms'],
    package_dir={'': 'src'},
    package_data={'rosdep2': ['20-default.list']},
    data_files=[
        (os.path.join(install_prefix, 'etc/ros/rosdep/sources.list.d'),
            ['src/rosdep2/20-default.list'])],
    install_requires=['catkin_pkg', 'rospkg', 'rosdistro >= 0.3.0', 'PyYAML >= 3.1'],
    setup_requires=['nose >= 1.0'],
    test_suite='nose.collector',
    test_requires=['mock'],
    scripts=['scripts/rosdep', 'scripts/rosdep-source'],
    author="Tully Foote, Ken Conley",
    author_email="foote@willowgarage.com, kwc@willowgarage.com",
    url="http://wiki.ros.org/rosdep",
    download_url="http://download.ros.org/downloads/rosdep/",
    keywords=['ROS'],
    classifiers=[
        "Programming Language :: Python",
        "License :: OSI Approved :: BSD License"],
    description="rosdep package manager abstrction tool for ROS",
    long_description="Command-line tool for installing system "
                     "dependencies on a variety of platforms.",
    license="BSD"
)
