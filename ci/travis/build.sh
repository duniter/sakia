#!/usr/bin/env bash

eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"

cd $HOME/build/ucoin-io/sakia
pyenv activate sakia-env
pip install coveralls
pip install cx_Freeze
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
    python setup.py bdist_dmg
elif [ $TRAVIS_OS_NAME == "linux" ]
then
    python setup.py build
    cp ~/.pyenv/versions/$PYENV_PYTHON_VERSION/lib/libpython3.*m.so.1.0 build/exe.linux-x86_64-3.4/
fi

