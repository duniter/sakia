#!/usr/bin/env bash

eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"

cd $HOME/build/ucoin-io/sakia
pyenv activate sakia-env

export XVFBARGS="-screen 0 1280x1024x24"
export DISPLAY=:99.0
sh -e /etc/init.d/xvfb start
sleep 3

coverage run --source=sakia.core,sakia.gui,sakia.models run_tests.py

