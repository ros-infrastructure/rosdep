#!/usr/bin/env python

import os
from setuptools import setup, find_packages

exec(open(os.path.join(os.path.dirname(__file__), 'src', 'rosinstall_generator', '__init__.py')).read())

setup(
    name='rosinstall_generator',
    version=__version__,
    install_requires=['argparse', 'distribute', 'rosdistro', 'rospkg', 'PyYAML'],
    packages=find_packages('src'),
    package_dir={'': 'src'},
    scripts=['bin/rosinstall_generator'],
    author='Dirk Thomas',
    author_email='dthomas@osrfoundation.org',
    maintainer='Dirk Thomas',
    maintainer_email='dthomas@osrfoundation.org',
    url='http://www.ros.org/wiki/rosinstall_generator',
    download_url='http://pr.willowgarage.com/downloads/rosinstall_generator/',
    keywords=['ROS'],
    classifiers=['Programming Language :: Python',
                 'License :: OSI Approved :: BSD License',
                 'License :: OSI Approved :: MIT License'],
    description="A tool to generator rosinstall files",
    long_description="""A tool to generator rosinstall files""",
    license='BSD'
)
