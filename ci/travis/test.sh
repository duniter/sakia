#!/usr/bin/env bash

eval "$(pyenv init -)"

if [ $TRAVIS_OS_NAME == "linux" ]
then
    export XVFBARGS="-screen 0 1280x1024x24"
    export DISPLAY=:99.0
    sh -e /etc/init.d/xvfb start
    sleep 3
fi

cd $HOME/build/duniter/sakia
pyenv shell $PYENV_PYTHON_VERSION
if [ $TRAVIS_OS_NAME == "linux" ]
then
    py.test --cov=sakia tests/
else
    py.test
fi


