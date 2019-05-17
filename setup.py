import os
from setuptools import setup

exec(open(os.path.join(os.path.dirname(__file__), 'src', 'rosdep2', '_version.py')).read())

setup(
    name='rosdep',
    version=__version__,  # noqa:F821
    packages=['rosdep2', 'rosdep2.platforms'],
    package_dir={'': 'src'},
    install_requires=['catkin_pkg >= 0.4.0', 'rospkg >= 1.1.8', 'rosdistro >= 0.7.0', 'PyYAML >= 3.1'],
    test_suite='nose.collector',
    test_requires=['mock', 'nose >= 1.0'],
    scripts=['scripts/rosdep', 'scripts/rosdep-source'],
    author='Tully Foote, Ken Conley',
    author_email='tfoote@osrfoundation.org',
    url='http://wiki.ros.org/rosdep',
    keywords=['ROS'],
    classifiers=[
        'Programming Language :: Python',
        'License :: OSI Approved :: BSD License'],
    description='rosdep package manager abstraction tool for ROS',
    long_description='Command-line tool for installing system '
                     'dependencies on a variety of platforms.',
    license='BSD'
)
