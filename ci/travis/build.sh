#!/usr/bin/env bash

export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"

cd $HOME/build/duniter/sakia

pyenv shell $PYENV_PYTHON_VERSION
pip install --upgrade pip
pyenv rehash
pip install coveralls
pip install pytest-cov
pip install pyinstaller==3.3.1
pip install -r requirements.txt
if [ $TRAVIS_OS_NAME == "linux" ]
then
    pip install -U git+https://github.com/posborne/dbus-python.git
    pip install notify2

    export PATH=/tmp/qt/5.8/5.8/gcc_64/bin:$PATH
fi
if [ $TRAVIS_OS_NAME == "osx" ]
then
    brew link --force qt5
    export PATH=/Users/travis/.pyenv/versions/$PYENV_PYTHON_VERSION/Python.framework/Versions/3.5/bin:$PATH
fi

echo $PATH
python gen_resources.py
python gen_translations.py --lrelease

if [ $TRAVIS_OS_NAME == "osx" ]
then
    pyinstaller sakia.spec
    cp -rv dist/sakia/* dist/sakia.app/Contents/MacOS
    cp -v res/osx/Info.plist dist/sakia.app/Contents/
    rm -rfv dist/sakia
elif [ $TRAVIS_OS_NAME == "linux" ]
then
    pyinstaller sakia.spec
    rm -f dist/sakia/libdrm.so.2
fi
