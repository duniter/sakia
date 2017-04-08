BEGIN TRANSACTION ;

ALTER TABLE transactions RENAME TO TempOldTransactions;

-- TRANSACTIONS TABLE
CREATE TABLE IF NOT EXISTS transactions(
                               currency VARCHAR(30),
                               pubkey VARCHAR(50),
                               sha_hash VARCHAR(50),
                               written_on INT,
                               blockstamp VARCHAR(100),
                               ts INT,
                               signatures VARCHAR(100),
                               issuers TEXT,
                               receivers TEXT,
                               amount INT,
                               amountbase INT,
                               comment VARCHAR(255),
                               txid INT,
                               state INT,
                               local BOOLEAN,
                               raw TEXT,
                               PRIMARY KEY (currency, pubkey, sha_hash)
                               );

DROP TABLE TempOldTransactions;

COMMIT;