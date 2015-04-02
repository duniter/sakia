cutecoin
========

Qt Client for [Ucoin](http://www.ucoin.io) project.


## Goal features
  * Ucoin account management via wallets and communities
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

### How to build
  * __git clone --recursive https://github.com/ucoin-io/cutecoin.git__
  * Dependencies :
   * [python3](https://www.python.org/downloads/)
   * [cx_freeze for python 3](http://cx-freeze.sourceforge.net/)
   * [pyqt5](http://www.riverbankcomputing.co.uk/software/pyqt/download5)
   * [libsodium](http://doc.libsodium.org/installation/README.html)
  * To get python libraries dependencies :
   * __pip install pylibscrypt__
   * __pip install libnacl__
   * __pip install requests__
   * __pip install base58__
  * Run __python gen_resources.py__ in cutecoin folder
  * Run __python setup.py build__ in cutecoin folder
  * The executable is generated in "build" folder, named "cutecoin"

### How to download latest release
  * Go to the [current release](https://github.com/ucoin-io/cutecoin/releases/tag/0.9.1)
  * Download the package corresponding to your operating system
  * Unzip and start "cutecoin" :)
  * Join our beta community by contacting us on ucoin forums : forum.ucoin.io
