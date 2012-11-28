from setuptools import setup

import sys
sys.path.insert(0, 'src')

from rosdep2 import __version__

setup(
    name='rosdep',
    version=__version__,
    packages=['rosdep2', 'rosdep2.platforms'],
    package_dir={'': 'src'},
    install_requires=['catkin_pkg', 'rospkg', 'PyYAML >= 3.1'],
    setup_requires=['nose >= 1.0'],
    test_suite='nose.collector',
    test_requires=['mock'],
    scripts=['scripts/rosdep'],
    author="Tully Foote, Ken Conley",
    author_email="foote@willowgarage.com, kwc@willowgarage.com",
    url="http://www.ros.org/wiki/rosdep",
    download_url="http://pr.willowgarage.com/downloads/rosdep/",
    keywords=['ROS'],
    classifiers=[
        "Programming Language :: Python",
        "License :: OSI Approved :: BSD License"],
    description="rosdep package manager abstrction tool for ROS",
    long_description="Command-line tool for installing system "
                     "dependencies on a variety of platforms.",
    license="BSD"
)
