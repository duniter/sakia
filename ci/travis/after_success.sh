#!/usr/bin/env bash

eval "$(pyenv init -)"

cd $HOME/build/duniter/sakia
pyenv shell $PYENV_PYTHON_VERSION

coverage -rm
coveralls