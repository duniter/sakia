#!/usr/bin/env bash

eval "$(pyenv init -)"

if [ $TRAVIS_OS_NAME == "linux" ]
then
    export XVFBARGS="-screen 0 1280x1024x24"
    export DISPLAY=:99.0
    sudo sh -e /etc/init.d/xvfb restart
    sleep 3
fi

cd $HOME/build/duniter/sakia
pyenv shell $PYENV_PYTHON_VERSION
if [ $TRAVIS_OS_NAME == "linux" ]
then
    coverage run --source=sakia.core,sakia.gui,sakia.models pytest
else
    pytest
fi


