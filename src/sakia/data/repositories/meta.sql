-- IDENTITY TABLE
CREATE TABLE IF NOT EXISTS identities(
                               currency VARCHAR(30),
                               pubkey VARCHAR(50),
                               uid VARCHAR(255),
                               blockstamp VARCHAR(100),
                               signature VARCHAR(100),
                               ts INT,
                               written BOOLEAN,
                               revoked BOOLEAN,
                               member BOOLEAN,
                               ms_buid VARCHAR(100),
                               ms_timestamp INT,
                               PRIMARY KEY (currency, pubkey, uid, blockstamp)
                               );

-- COMMUNITY TABLE
CREATE TABLE IF NOT EXISTS communities(
                               c FLOAT(1,6),
                               dt INT,
                               ud0 INT,
                               sig_period INT,
                               sig_stock INT,
                               sig_window INT,
                               sig_validity INT,
                               sig_qty INT,
                               xpercent FLOAT(1,6),
                               ms_validity INT,
                               step_max INT,
                               median_time_blocks INT,
                               avg_gen_time INT,
                               dt_diff_eval INT,
                               blocks_rot INT,
                               percent_rot FLOAT(1,6),
                               currency VARCHAR(30),
                               PRIMARY KEY (currency)
                               );
-- IDENTITY TABLE
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
