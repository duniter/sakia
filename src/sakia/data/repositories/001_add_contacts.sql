BEGIN TRANSACTION ;

-- CONTACTS TABLE
CREATE TABLE IF NOT EXISTS contacts (
   currency       VARCHAR(255),
   name           VARCHAR(255),
   pubkey         VARCHAR(255),
   fields         TEXT,
   contact_id     INTEGER PRIMARY KEY
);

COMMIT;