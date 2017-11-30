#!/usr/bin/env bash

export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"

if [ $TRAVIS_OS_NAME == "linux" ]
then
    export XVFBARGS="-screen 0 1280x1024x24"
    export DISPLAY=:99.0
    sh -e /etc/init.d/xvfb start
    sleep 3
fi

if [ $TRAVIS_OS_NAME == "osx" ]
then
    brew link --force qt5
    export PATH=/Users/travis/.pyenv/versions/$PYENV_PYTHON_VERSION/Python.framework/Versions/3.5/bin:$PATH
fi

cd $HOME/build/duniter/sakia
pyenv shell $PYENV_PYTHON_VERSION
if [ $TRAVIS_OS_NAME == "linux" ]
then
    py.test --cov=sakia tests/
else
    py.test -s
fi


