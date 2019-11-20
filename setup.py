import os
from setuptools import setup

kwargs = {
    'name': 'rosdep',
    # same version as in:
    # - src/rosdep2/__init__.py
    # - stdeb.cfg
    'version': '0.18.0',
    'packages': ['rosdep2', 'rosdep2.ament_packages', 'rosdep2.platforms'],
    'package_dir': {'': 'src'},
    'install_requires': ['catkin_pkg >= 0.4.0', 'rospkg >= 1.1.10', 'rosdistro >= 0.7.5', 'PyYAML >= 3.1'],
    'test_suite': 'nose.collector',
    'test_requires': ['mock', 'nose >= 1.0'],
    'scripts': ['scripts/rosdep', 'scripts/rosdep-source'],
    'author': 'Tully Foote, Ken Conley',
    'author_email': 'tfoote@osrfoundation.org',
    'url': 'http://wiki.ros.org/rosdep',
    'keywords': ['ROS'],
    'classifiers': [
        'Programming Language :: Python',
        'License :: OSI Approved :: BSD License'],
    'description': 'rosdep package manager abstraction tool for ROS',
    'long_description': 'Command-line tool for installing system '
                        'dependencies on a variety of platforms.',
    'license': 'BSD',
}
if 'SKIP_PYTHON_MODULES' in os.environ:
    kwargs['packages'] = []
    kwargs['package_dir'] = {}
if 'SKIP_PYTHON_SCRIPTS' in os.environ:
    kwargs['name'] += '_modules'
    kwargs['scripts'] = {}

setup(**kwargs)
