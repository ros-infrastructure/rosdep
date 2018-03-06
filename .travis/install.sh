#!/bin/bash

if [[ $TRAVIS_OS_NAME == 'osx' ]]; then
    # Install pyenv
    brew install pyenv-virtualenv
    pyenv versions
    eval "$(pyenv init -)"
    pyenv install $TRAVIS_PYTHON_VERSION
    PYTHON_ENV_NAME=virtual-env-$TRAVIS_PYTHON_VERSION
    pyenv virtualenv $TRAVIS_PYTHON_VERSION $PYTHON_ENV_NAME
    pyenv activate $PYTHON_ENV_NAME
fi
