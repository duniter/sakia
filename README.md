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

### Todo
  * Creating a list of received and sent transactions
  * ... ?

### How to install
  * __git clone --recursive https://github.com/Insoleet/cutecoin.git__
  * Install [python3](https://www.python.org/downloads/), [cx_freeze for python 3](http://cx-freeze.sourceforge.net/) and [pyqt5](http://www.riverbankcomputing.co.uk/software/pyqt/download5), and [pip](http://www.pip-installer.org/en/latest/)
  * Run :
   * __pip install pylibscrypt__
   * __pip install libnacl__
   * __pip install requests__
  * Run __python gen_resources.py__ in cutecoin folder
  * Run __python setup.py build__ in cutecoin folder
  * The executable is generated in "build" folder, named "__init__"
