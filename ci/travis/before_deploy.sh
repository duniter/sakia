#!/usr/bin/env bash

[ $TRAVIS_OS_NAME == "osx" ] && zip -r sakia-${TRAVIS_OS_NAME}.zip build/*.dmg
[ $TRAVIS_OS_NAME == "linux" ] && zip -r sakia-${TRAVIS_OS_NAME}.zip build/exe*
