.PHONY: all setup clean_dist distro clean install

NAME=rosinstall_generator
VERSION=`./setup.py --version`

all:
	echo "noop for debbuild"

setup:
	echo "building version ${VERSION}"

clean_dist:
	-rm -f MANIFEST
	-rm -rf deb_dist
	-rm -rf dist
	-rm -rf src/rosinstall_generator.egg-info

distro: setup clean_dist
	python setup.py sdist

clean: clean_dist
	echo "clean"

install: distro
	sudo checkinstall python setup.py install
