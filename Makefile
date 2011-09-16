.PHONY: all setup clean_dist distro clean install dsc source_deb upload

NAME='rosdep'
VERSION='0.0.1'

all:
	echo "noop for debbuild"

setup:
	echo "confirming version numbers are all consistent"
	grep ${VERSION} setup.py
	echo "building version ${VERSION}"

clean_dist:
	-rm -f MANIFEST
	-rm -rf dist
	-rm -rf deb_dist

distro: setup clean_dist
	python setup.py sdist

push: distro
	python setup.py sdist register upload
	scp dist/${NAME}-${VERSION}.tar.gz ipr:/var/www/pr.willowgarage.com/html/downloads/${NAME}

clean: clean_dist
	echo "clean"

install: distro
	sudo checkinstall python setup.py install

dsc: distro
	python setup.py --command-packages=stdeb.command sdist_dsc

source_deb: dsc
	# need to convert unstable to each distro and repeat
	cd deb_dist/${NAME}-${VERSION} && dpkg-buildpackage -sa -k84C5CECD

binary_deb: dsc
	# need to convert unstable to each distro and repeat
	cd deb_dist/${NAME}-${VERSION} && dpkg-buildpackage -sa -k84C5CECD

testsetup:
	echo "running rosdep tests"

test: testsetup
	nosetests --with-coverage --cover-package=rosdep2 --with-xunit
