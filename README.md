cutecoin
========

Qt Client for [Ucoin](http://www.ucoin.io) project.


## Goal features
  * Ucoin account management via wallets and communities
  * Multi-currency
  * Multi-community
  * Multi-wallets
  * Contacts messaging
  * User-friendly coins transfer
  * On-the-fly and automatic coins fusion and divisions for transactions
  * Coins issuance policies : minimal space, minimal changes
  * Community membership management via a voting interface

## Current state
### Done (master branch)
  * Accounts management
  * Communities viewing
  * Coins Transfer
  * cx_freeze deployment
  * Wallet management (no multiple wallets yet)
  * Contacts management

### Todo
  * Joining a community, publishing keys
  * Multiple wallets management
  * Cutecoin keyring

### How to install
  * __git clone --recursive https://github.com/Insoleet/cutecoin.git__
  * Note : On Windows, it seems that PyQt5 works best with 32 bits version of Python.
  * Install [python3.3](https://www.python.org/download/releases/3.3.5), [cx_freeze for python 3.3](http://cx-freeze.sourceforge.net/) and [pyqt5](http://www.riverbankcomputing.co.uk/software/pyqt/download5), and [pip](http://www.pip-installer.org/en/latest/)
  * On Linux, deployment works with python3.4 too
  * On Windows, make sure folders for python3 and pyqt5 binaries are in your $PATH
  * Run __pip install python-gnupg__ and __pip install requests__
  * Run __python gen_resources.py__ in cutecoin folder
  * Run __python setup.py build__ in cutecoin folder
  * The executable is generated in "build" folder, named "__init__"
