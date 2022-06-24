import os
from setuptools import setup

kwargs = {
    'name': 'rosdep',
    # same version as in:
    # - src/rosdep2/__init__.py
    # - stdeb.cfg
    'version': '0.22.0',
    'packages': ['rosdep2', 'rosdep2.ament_packages', 'rosdep2.platforms'],
    'package_dir': {'': 'src'},
    'install_requires': ['catkin_pkg >= 0.4.0', 'rospkg >= 1.4.0', 'rosdistro >= 0.7.5', 'PyYAML >= 3.1', 'setuptools'],
    'extras_require': {
        'test': [
            'flake8',
            'flake8-comprehensions',
            "mock; python_version < '3.3'",
            'pytest',
        ],
    },
    'author': 'Tully Foote, Ken Conley',
    'author_email': 'tfoote@osrfoundation.org',
    'maintainer': 'ROS Infrastructure Team',
    'project_urls': {
        'Source code':
        'https://github.com/ros-infrastructure/rosdep',
        'Issue tracker':
        'https://github.com/ros-infrastructure/rosdep/issues',
    },
    'url': 'http://wiki.ros.org/rosdep',
    'keywords': ['ROS'],
    'entry_points': {
        'console_scripts': [
            'rosdep = rosdep2.main:rosdep_main',
            'rosdep-source = rosdep2.install:install_main'
        ]
    },
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
    kwargs['entry_points'] = {}

setup(**kwargs)
