#!/usr/bin/env bash

eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"

cd $HOME/build/ucoin-io/sakia
pyenv activate sakia-env

if [ $TRAVIS_OS_NAME == "linux" ]
then
    export XVFBARGS="-screen 0 1280x1024x24"
    export DISPLAY=:99.0
    sh -e /etc/init.d/xvfb start
    sleep 3
fi

PYTHONPATH=$HOME/build/ucoin-io/sakia/src coverage run --source=sakia.core,sakia.gui,sakia.models \
    python -m unittest discover --start-directory src/sakia/tests

