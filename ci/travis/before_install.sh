#!/usr/bin/env bash


if [ $TRAVIS_OS_NAME == "linux" ]
then
    export XVFBARGS="-screen 0 1280x1024x24"
    export DISPLAY=:99.0
    sh -e /etc/init.d/xvfb start
    sleep 3
fi

if [ $TRAVIS_OS_NAME == "osx" ]
then
    brew update
    brew install libsodium
    ## Ensure your brew QT version is up to date. (brew install qt -> qt 4.8)
    brew install qt5
    brew list qt5
    brew install pyenv-virtualenv
elif [ $TRAVIS_OS_NAME == "linux" ]
then
    sudo apt-get update
    sudo apt-get install -qq -y libxcb1 libxcb1-dev libx11-xcb1 libx11-xcb-dev libxcb-keysyms1 libxcb-keysyms1-dev libxcb-image0 \
            libxcb-image0-dev libxcb-shm0 libxcb-shm0-dev libxcb-icccm4 libxcb-icccm4-dev \
            libxcb-xfixes0-dev libxrender-dev libxcb-shape0-dev libxcb-randr0-dev libxcb-render-util0 \
            libxcb-render-util0-dev libxcb-glx0-dev libgl1-mesa-dri libegl1-mesa libpcre3 libgles2-mesa-dev \
            freeglut3-dev libfreetype6-dev xorg-dev xserver-xorg-input-void xserver-xorg-video-dummy xpra libosmesa6-dev \
            curl libdbus-1-dev libdbus-glib-1-dev autoconf automake libtool libgstreamer-plugins-base0.10-0 dunst fakeroot \
            dbus-x11
    wget https://download.qt.io/official_releases/qt/5.9/5.9.4/qt-opensource-linux-x64-5.9.4.run
    chmod +x qt-opensource-linux-x64-5.9.4.run
    ./qt-opensource-linux-x64-5.9.4.run --script $HOME/build/duniter/sakia/ci/travis/qt-installer-noninteractive.qs

    wget http://archive.ubuntu.com/ubuntu/pool/universe/libs/libsodium/libsodium18_1.0.13-1_amd64.deb
    sudo dpkg -i libsodium18_1.0.13-1_amd64.deb
    rm -r ~/.pyenv
    git clone https://github.com/pyenv/pyenv.git ~/.pyenv
    echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bash_profile
    echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bash_profile
    export PYENV_ROOT="$HOME/.pyenv"
    export PATH="$PYENV_ROOT/bin:$PATH"
    ldconfig -p
    #export $(dbus-launch)

fi

eval "$(pyenv init -)"

pyenv update
pyenv install --list
if [ $TRAVIS_OS_NAME == "osx" ]
then
    env PYTHON_CONFIGURE_OPTS="--enable-framework" pyenv install $PYENV_PYTHON_VERSION
elif [ $TRAVIS_OS_NAME == "linux" ]
then
    PYTHON_CONFIGURE_OPTS="--enable-shared" pyenv install --force $PYENV_PYTHON_VERSION
fi

pyenv shell $PYENV_PYTHON_VERSION

cd $HOME
