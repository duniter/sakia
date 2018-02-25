#!/usr/bin/env bash

if [ $TRAVIS_OS_NAME == "osx" ]
then
    zip -r sakia-${TRAVIS_OS_NAME}.zip dist/sakia.app/
elif [ $TRAVIS_OS_NAME == "linux" ]
then
    zip -r sakia-${TRAVIS_OS_NAME}.zip dist/sakia/

    # Debian package
    chmod 755 ci/travis/debian/DEBIAN/post*
    chmod 755 ci/travis/debian/DEBIAN/pre*
    mkdir -p ci/travis/debian/opt/sakia

    cp sakia.png ci/travis/debian/opt/sakia/
    cp sakia-${TRAVIS_OS_NAME}.zip ci/travis/debian/opt/sakia/sakia.zip
    cp -r res/linux/usr ci/travis/debian
    fakeroot dpkg-deb --build ci/travis/debian
    mv ci/travis/debian.deb sakia-${TRAVIS_OS_NAME}.deb
fi
