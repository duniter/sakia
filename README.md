<!-- Landscape | [![Code Health](https://landscape.io/github/duniter/sakia/dev/landscape.svg?style=flat)](https://landscape.io/github/duniter/sakia/dev) -->

![sakia logo](https://raw.github.com/duniter/sakia/master/sakia.png)

# Sakia
 [![coverage report](https://git.duniter.org/clients/python/sakia/badges/gitlab/coverage.svg)](https://git.duniter.org/clients/python/sakia/commits/gitlab)
 [![pipeline status](https://git.duniter.org/clients/python/sakia/badges/gitlab/pipeline.svg)](https://git.duniter.org/clients/python/sakia/commits/gitlab)
 [![Build Status](https://travis-ci.org/duniter/sakia.svg?branch=travis)](https://travis-ci.org/duniter/sakia)
 [![Build status](https://ci.appveyor.com/api/projects/status/pvl18xon8pvu2c8w/branch/dev?svg=true)](https://ci.appveyor.com/project/Insoleet/sakia-bee4m/branch/dev)

========

Python3 and PyQt5 Client for [duniter](http://www.duniter.org) project.


### Features
  * Accounts management
  * Communities viewing
  * Money Transfer
  * cx_freeze deployment
  * Wallets management
  * Contacts management
  * Joining a community, publishing keys
  * Multiple wallets management

### Dependencies
  * Dependencies :
   * Qt5
   * [python3](https://www.python.org/downloads/)
   * [libsodium](http://doc.libsodium.org/installation/README.html)

  * General tips : use pyenv to build sakia, as described in the [wiki](https://github.com/duniter/sakia/wiki/Cutecoin-install-for-developpers)

### Wheel Build scripts
  * Install __wheel__ with `pip install wheel`
  * Run `python3 gen_resources.py` in sakia folder
  * Run `python3 gen_translations.py` in sakia folder
  * To build the wheel : Run `python3 setup.py bdist_wheel` in sakia folder
  
### Pyinstaller Build scripts
  * Install __pyinstaller__ with `pip install pyinstaller`
  * Run `python3 gen_resources.py` in sakia folder
  * Run `python3 gen_translations.py` in sakia folder
  * To build the binaries : Run `pyinstall sakia.spec`

### Install with pip
  * Run `pip install sakia`
  * start "sakia" :)
 
### Download latest release
  * Go to [current release](https://github.com/duniter/sakia/releases)
  * Download corresponding package to your operating system
  * Unzip and start "sakia" :)
  * Join our beta community by contacting us on [duniter forum](http://forum.duniter.org/)

## License
This software is distributed under [GNU GPLv3](https://raw.github.com/duniter/sakia/dev/LICENSE).
