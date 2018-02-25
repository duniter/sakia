#!/usr/bin/env bash

export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"

cd $HOME/build/duniter/sakia
pyenv shell $PYENV_PYTHON_VERSION

coverage -rm
coveralls