#!/usr/bin/env bash

eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"

cd $HOME/build/ucoin-io/sakia
pyenv activate sakia-env
pip install coveralls
pip install https://github.com/pyinstaller/pyinstaller/archive/develop.zip
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
    pyi-makespec src/sakia/main.py --debug --additional-hooks-dir hooks
    cat main.spec
elif [ $TRAVIS_OS_NAME == "linux" ]
then
    pyinstaller src/sakia/main.py --debug --additional-hooks-dir hooks
fi

