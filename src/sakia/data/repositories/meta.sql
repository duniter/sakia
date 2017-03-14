-- IDENTITY TABLE
CREATE TABLE IF NOT EXISTS identities(
                               currency VARCHAR(30),
                               pubkey VARCHAR(50),
                               uid VARCHAR(255),
                               blockstamp VARCHAR(100),
                               signature VARCHAR(100),
                               timestamp INT,
                               written BOOLEAN,
                               revoked_on INT,
                               outdistanced BOOLEAN,
                               member BOOLEAN,
                               ms_buid VARCHAR(100),
                               ms_timestamp INT,
                               ms_written_on INT,
                               ms_type VARCHAR(5),
                               PRIMARY KEY (currency, pubkey, uid, blockstamp)
                               );

-- BLOCKCHAIN TABLE
CREATE TABLE IF NOT EXISTS blockchains (
  c                             FLOAT(1, 6),
  dt                            INT,
  ud0                           INT,
  sig_period                    INT,
  sig_stock                     INT,
  sig_window                    INT,
  idty_window                   INT,
  ms_window                     INT,
  sig_validity                  INT,
  sig_qty                       INT,
  xpercent                      FLOAT(1, 6),
  ms_validity                   INT,
  step_max                      INT,
  median_time_blocks            INT,
  avg_gen_time                  INT,
  dt_diff_eval                  INT,
  percent_rot                   FLOAT(1, 6),
  current_buid            INT,
  current_members_count   INT,
  current_mass            INT,
  median_time             INT,
  last_members_count      INT,
  last_ud                 INT,
  last_ud_base            INT,
  last_ud_time            INT,
  previous_mass           INT,
  previous_members_count  INT,
  previous_ud             INT,
  previous_ud_base        INT,
  previous_ud_time        INT,
  currency                VARCHAR(30),
  PRIMARY KEY (currency)
);


-- CERTIFICATIONS TABLE
CREATE TABLE IF NOT EXISTS certifications(
                               currency VARCHAR(30),
                               certifier VARCHAR(50),
                               certified VARCHAR(50),
                               block INT,
                               ts INT,
                               signature VARCHAR(100),
                               written_on INT,
                               PRIMARY KEY (currency, certifier, certified, block)
                               );

-- TRANSACTIONS TABLE
CREATE TABLE IF NOT EXISTS transactions(
                               currency VARCHAR(30),
                               sha_hash VARCHAR(50),
                               written_on INT,
                               blockstamp VARCHAR(100),
                               ts INT,
                               signature VARCHAR(100),
                               issuer VARCHAR(50),
                               receiver TEXT,
                               amount INT,
                               amountbase INT,
                               comment VARCHAR(255),
                               txid INT,
                               state INT,
                               local BOOLEAN,
                               raw TEXT,
                               PRIMARY KEY (sha_hash)
                               );

-- NODES TABLE
CREATE TABLE IF NOT EXISTS nodes(
                               currency             VARCHAR(30),
                               pubkey               VARCHAR(50),
                               endpoints            TEXT,
                               peer_buid            VARCHAR(100),
                               uid                  VARCHAR(50),
                               current_buid         VARCHAR(100),
                               current_ts           INT,
                               previous_buid        VARCHAR(100),
                               state                INT,
                               software             VARCHAR(100),
                               version              VARCHAR(50),
                               merkle_peers_root    VARCHAR(50),
                               merkle_peers_leaves  TEXT,
                               root                 BOOLEAN,
                               member               BOOLEAN,
                               PRIMARY KEY (currency, pubkey)
                               );

-- Cnnections TABLE
CREATE TABLE IF NOT EXISTS connections(
                               currency           VARCHAR(30),
                               pubkey             VARCHAR(50),
                               uid                VARCHAR(255),
                               scrypt_N           INT,
                               scrypt_p           INT,
                               scrypt_r           INT,
                               blockstamp         VARCHAR(100),
                               PRIMARY KEY (currency, pubkey)
                               );

-- Cnnections TABLE
CREATE TABLE IF NOT EXISTS sources(
                               currency           VARCHAR(30),
                               pubkey             VARCHAR(50),
                               identifier         VARCHAR(255),
                               noffset             INT,
                               type               VARCHAR(8),
                               amount             INT,
                               base               INT,
                               PRIMARY KEY (currency, pubkey, identifier, noffset)
                               );

CREATE TABLE IF NOT EXISTS dividends(
                               currency           VARCHAR(30),
                               pubkey             VARCHAR(50),
                               block_number       VARCHAR(255),
                               timestamp          INT,
                               amount             INT,
                               base               INT,
                               PRIMARY KEY (currency, pubkey, block_number)
);

