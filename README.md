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
  * Coins issuance
  * Coins Transfer
  * cx_freeze deployment

### Work in progress (dev branch)
  * Contacts management
  * Account THT management

### Todo
  * Coins issuance policies
  * Contacts and messaging
  * Separating the 3 roles : Voter, Member, Random guy. Differnt rights for different roles :
    * A voter should be able to access the voting UI of the community (+member and random guy rights)
    * A member should be able to issue money (+random guy rights)
    * A random guy should be able to send and receive money
