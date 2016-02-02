#!/usr/bin/env bash

eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"

cd $HOME/build/ucoin-io/sakia
pyenv activate sakia-env
pip install coveralls
pip install pyinstaller
pip install -r requirements.txt
if [ $TRAVIS_OS_NAME == "linux" ]
then
    pip install -U git+https://github.com/posborne/dbus-python.git
    pip install notify2
fi

python gen_resources.py
python gen_translations.py

if [ $TRAVIS_OS_NAME == "osx" ]
then
    pyinstaller sakia.spec
    cp -rv dist/sakia/* dist/sakia.app/Contents/MacOS
    rm -rfv dist/sakia
elif [ $TRAVIS_OS_NAME == "linux" ]
then
    pyinstaller sakia.spec
fi

