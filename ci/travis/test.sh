#!/usr/bin/env bash

eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"

if [ $TRAVIS_OS_NAME == "linux" ]
then
    export XVFBARGS="-screen 0 1280x1024x24"
    export DISPLAY=:99.0
    sh -e /etc/init.d/xvfb restart
    sleep 3
fi

cd $HOME/build/ucoin-io/sakia
pyenv activate sakia-env
coverage run --source=sakia.core,sakia.gui,sakia.models setup.py test

