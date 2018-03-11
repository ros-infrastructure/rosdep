#!/bin/bash

do_install()
{
    set -e

    if [[ $TRAVIS_OS_NAME == 'osx' && $PYTHON_INSTALLER == 'pyenv' ]]; then
        brew install pyenv-virtualenv
        pyenv versions
        eval "$(pyenv init -)"
        pyenv install $TRAVIS_PYTHON_VERSION
        PYTHON_ENV_NAME=virtual-env-$TRAVIS_PYTHON_VERSION
        pyenv virtualenv $TRAVIS_PYTHON_VERSION $PYTHON_ENV_NAME
        pyenv activate $PYTHON_ENV_NAME

    elif [[ $TRAVIS_OS_NAME == 'osx' && $PYTHON_INSTALLER == 'brew' ]]; then
        # nose 1.3.7 creates /usr/local/man dir if it does not exist.
        # The operation fails because current user does not own /usr/local.  Create the dir manually instead.
        sudo mkdir /usr/local/man
        sudo chown -R $(whoami) $(brew --prefix)/*

        export PATH=$(pwd)/.travis/shim:$PATH

        mkdir -p ~/Library/Python/2.7/lib/python/site-packages
        echo "$(brew --prefix)/lib/python2.7/site-packages" >> ~/Library/Python/2.7/lib/python/site-packages/homebrew.pth
    fi
}

do_install
