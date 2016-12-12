#!/usr/bin/env python

import os
from setuptools import setup, find_packages

exec(open(os.path.join(os.path.dirname(__file__), 'src', 'rosinstall_generator', '__init__.py')).read())

setup(
    name='rosinstall_generator',
    version=__version__,
    install_requires=['argparse', 'catkin_pkg >= 0.1.28', 'rosdistro >= 0.5.0', 'rospkg', 'PyYAML', 'setuptools'],
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
    description="A tool to generator rosinstall files",
    long_description="""A tool to generator rosinstall files""",
    license='BSD'
)
