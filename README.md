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
  * Wallet management (no multiple wallets yet)
  * Contacts management

### Todo
  * Joining a community, publishing keys
  * Multiple wallets management

### How to install
  * __git clone --recursive https://github.com/Insoleet/cutecoin.git__
  * Note : On Windows, this can't be installed because of Pynacl not available on this OS. Issue #100 opened : https://github.com/pyca/pynacl/issues/100 )
  * Install [python3](https://www.python.org/downloads/), [cx_freeze for python 3](http://cx-freeze.sourceforge.net/) and [pyqt5](http://www.riverbankcomputing.co.uk/software/pyqt/download5), and [pip](http://www.pip-installer.org/en/latest/)
  * Run :
   * __pip install scrypt__
   * __pip install pynacl__
   * __pip install requests__
  * Run __python gen_resources.py__ in cutecoin folder
  * Run __python setup.py build__ in cutecoin folder
  * The executable is generated in "build" folder, named "__init__"
