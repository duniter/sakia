-- IDENTITY TABLE
CREATE TABLE IF NOT EXISTS identities(
                               currency VARCHAR(30),
                               pubkey VARCHAR(50),
                               uid VARCHAR(255),
                               blockstamp VARCHAR(100),
                               signature VARCHAR(100),
                               ts INT,
                               written_on VARCHAR(100),
                               revoked_on VARCHAR(100),
                               member BOOLEAN,
                               ms_buid VARCHAR(100),
                               ms_timestamp INT,
                               ms_written_on VARCHAR(100),
                               ms_type VARCHAR(5),
                               PRIMARY KEY (currency, pubkey, uid, blockstamp)
                               );

-- COMMUNITIES TABLE
CREATE TABLE IF NOT EXISTS communities (
  c                  FLOAT(1, 6),
  dt                 INT,
  ud0                INT,
  sig_period         INT,
  sig_stock          INT,
  sig_window         INT,
  sig_validity       INT,
  sig_qty            INT,
  xpercent           FLOAT(1, 6),
  ms_validity        INT,
  step_max           INT,
  median_time_blocks INT,
  avg_gen_time       INT,
  dt_diff_eval       INT,
  blocks_rot         INT,
  percent_rot        FLOAT(1, 6),
  currency           VARCHAR(30),
  PRIMARY KEY (currency)
);

-- BLOCKCHAIN TABLE
CREATE TABLE IF NOT EXISTS blockchains (
  current_buid INT,
  nb_members    INT,
  current_mass  INT,
  median_time   INT,
  last_ud       INT,
  last_ud_base  INT,
  previous_mass INT,
  currency      VARCHAR(30),
  PRIMARY KEY (currency)
);


-- CERTIFICATIONS TABLE
CREATE TABLE IF NOT EXISTS certifications(
                               currency VARCHAR(30),
                               certifier VARCHAR(50),
                               certified VARCHAR(50),
                               blockstamp VARCHAR(100),
                               ts INT,
                               signature VARCHAR(100),
                               written_on VARCHAR(100),
                               PRIMARY KEY (currency, certifier, certified, blockstamp)
                               );

-- TRANSACTIONS TABLE
CREATE TABLE IF NOT EXISTS transactions(
                               currency VARCHAR(30),
                               sha_hash VARCHAR(50),
                               written_on VARCHAR(100),
                               blockstamp VARCHAR(100),
                               ts INT,
                               signature VARCHAR(100),
                               issuer VARCHAR(50),
                               receiver VARCHAR(50),
                               amount INT,
                               amountbase INT,
                               comment VARCHAR(255),
                               txid INT,
                               PRIMARY KEY (sha_hash)
                               );

-- NODES TABLE
CREATE TABLE IF NOT EXISTS nodes(
                               currency       VARCHAR(30),
                               pubkey         VARCHAR(50),
                               endpoints      TEXT,
                               current_buid   VARCHAR(100),
                               previous_buid  VARCHAR(100),
                               state          INT,
                               software       VARCHAR(100),
                               version        VARCHAR(50),
                               merkle_nodes   TEXT,
                               PRIMARY KEY (currency, pubkey)
                               );
