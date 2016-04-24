#!/usr/bin/env bash

eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"

cd $HOME/build/duniter-io/sakia
pyenv activate sakia-env

coverage -rm
coveralls