BEGIN TRANSACTION ;

ALTER TABLE blockchains RENAME TO TempOldBlockchains;

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
  ud_time_0                     INT,
  ud_reeval_time_0              INT,
  dt_reeval                     INT,
  current_buid            INT,
  current_members_count   INT,
  current_mass            INT,
  median_time             INT,
-- NEW ENTRY : last_mass
  last_mass               INT,
-- END OF INSERT
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

-- We drop old blockchain data to force reinit on startup
DROP TABLE TempOldBlockchains;

COMMIT;