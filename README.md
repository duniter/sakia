<!-- Landscape | [![Code Health](https://landscape.io/github/duniter/sakia/dev/landscape.svg?style=flat)](https://landscape.io/github/duniter/sakia/dev) -->

![sakia logo](https://raw.github.com/duniter/sakia/master/sakia.png)

# Sakia
 [![pipeline status](https://git.duniter.org/clients/python/sakia/badges/gitlab/pipeline.svg)](https://git.duniter.org/clients/python/sakia/commits/gitlab)
 [![Build Status](https://travis-ci.org/duniter/sakia.svg?branch=travis)](https://travis-ci.org/duniter/sakia)
 [![Build status](https://ci.appveyor.com/api/projects/status/pvl18xon8pvu2c8w/branch/dev?svg=true)](https://ci.appveyor.com/project/Insoleet/sakia-bee4m/branch/dev)

========

Python3 and PyQt5 Client for [duniter](http://www.duniter.org) project.


## Goal features
  * duniter account management via wallets and communities
  * Multi-currency
  * Multi-community
  * Multi-wallets
  * Contacts management
  * User-friendly money transfer
  * Community membership management

## Current state
### Done (master branch)
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
   * [python3](https://www.python.org/downloads/)
   * [cx_freeze for python 3](http://cx-freeze.sourceforge.net/)
   * [pyqt5](http://www.riverbankcomputing.co.uk/software/pyqt/download5)
   * [libsodium](http://doc.libsodium.org/installation/README.html)
  * Python libraries dependencies :
   * __duniterpy__

  * General tips : use pyenv to build sakia, as described in the [wiki](https://github.com/duniter/sakia/wiki/Cutecoin-install-for-developpers)

### Build scripts
  * Run __python3 gen_resources.py__ in sakia folder
  * Run __python3 gen_translations.py__ in sakia folder
  * Run __python3 setup.py build__ in sakia folder
  * The executable is generated in "build" folder, named "sakia"

### Download latest release
  * Go to [current release](https://github.com/duniter/sakia/releases)
  * Download corresponding package to your operating system
  * Unzip and start "sakia" :)
  * Join our beta community by contacting us on [duniter forum](http://forum.duniter.org/)

## License
This software is distributed under [GNU GPLv3](https://raw.github.com/duniter/sakia/dev/LICENSE).
