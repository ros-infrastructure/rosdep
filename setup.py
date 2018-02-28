#!/usr/bin/env python

import os
import sys
from setuptools import setup, find_packages

install_requires=['catkin_pkg >= 0.1.28', 'rosdistro >= 0.6.8', 'rospkg', 'PyYAML', 'setuptools']

# argparse is a part of the standard library since python 2.7
if sys.version_info[0] == 2 and sys.version_info[1] <= 6:
    install_requires.append('argparse')

exec(open(os.path.join(os.path.dirname(__file__), 'src', 'rosinstall_generator', '__init__.py')).read())

setup(
    name='rosinstall_generator',
    version=__version__,
    install_requires=install_requires,
    packages=find_packages('src'),
    package_dir={'': 'src'},
    scripts=['bin/rosinstall_generator'],
    author='Dirk Thomas',
    author_email='dthomas@osrfoundation.org',
    maintainer='Dirk Thomas',
    maintainer_email='dthomas@osrfoundation.org',
    url='http://wiki.ros.org/rosinstall_generator',
    download_url='http://download.ros.org/downloads/rosinstall_generator/',
    keywords=['ROS'],
    classifiers=['Programming Language :: Python',
                 'License :: OSI Approved :: BSD License',
                 'License :: OSI Approved :: MIT License'],
    description="A tool for generating rosinstall files",
    long_description="""A tool for generating rosinstall files""",
    license='BSD'
)
