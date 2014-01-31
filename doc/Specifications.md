# Specifications

## Client-side concepts

### Account
 * An account is a PGP Key
 * An account can be a member of multiple communities
 * An account own at least one wallet for each currency he owns
 * An account can own multiple wallets of the same currency
 * An account must declare the nodes he trusts to receive transactions
 * An account must declare the nodes he uses to send transactions for a currency type

### Community
 * A community uses one unique currency
 * A community has members
 * Each members of the community can issue currency following the rule defined in the community amendment

### Wallets
 * Wallets can own only one type of currency
 * Wallets value are the sum of the transactions received and sent that the user listed in this wallet
 