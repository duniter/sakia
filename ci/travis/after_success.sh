#!/usr/bin/env bash
eval "$(pyenv virtualenv-init -)"

cd $HOME/ucoin-io/sakia
pyenv activate sakia-env

coverage -rm
coveralls