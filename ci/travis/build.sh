#!/usr/bin/env bash

eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"

cd $HOME/build/ucoin-io/sakia
pyenv activate sakia-env
pip install coveralls cx_Freeze
pip install -r requirements.txt
python gen_resources.py
python gen_translations.py

if [ $TRAVIS_OS_NAME == "osx" ]
then
    python setup.py bdist_dmg
elif [ $TRAVIS_OS_NAME == "linux" ]
then
    python setup.py build
fi

