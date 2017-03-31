BEGIN TRANSACTION ;

ALTER TABLE Nodes ADD COLUMN last_state_change INTEGER DEFAULT 0;
UPDATE NODES SET last_state_change=strftime('%s', 'now');
UPDATE NODES SET state=1 WHERE state=3 ;

COMMIT;
