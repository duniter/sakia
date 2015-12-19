#!/usr/bin/env bash

if [ $TRAVIS_OS_NAME == "osx" ]
then
    zip -r sakia-${TRAVIS_OS_NAME}.zip build/*.dmg
elif [ $TRAVIS_OS_NAME == "linux" ]
then
    zip -r sakia-${TRAVIS_OS_NAME}.zip build/exe*
fi
