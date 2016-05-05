#!/bin/bash

#__version_info__ = ('0', '20', '0dev6')
current=`grep -P "__version_info__ = \(\'\d+\', \'\d+\', \'\d+(\w*)\'\)" src/sakia/__init__.py | grep -oP "\'\d+\', \'\d+\', \'\d+(\w*)\'"`
echo "Current version: $current"

if [[ $1 =~ ^[0-9]+.[0-9]+.[0-9a-z]+$ ]]; then
  IFS='.' read -r -a array <<< "$1"
  sed -i "s/__version_info__\ = ($current)/__version_info__ = ('${array[0]}', '${array[1]}', '${array[2]}')/g" src/sakia/__init__.py
  git commit src/sakia/__init__.py -m "$2"
  git tag "$2"
else
  echo "Wrong version format"
fi
