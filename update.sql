INSERT INTO "groups" VALUES ('PUS','Kiel - Eckernförde Schulzentrum');

UPDATE members
	SET groupID = 'PUS';

UPDATE members
  SET active = true
  WHERE active = 'true';

UPDATE members
  SET active = false
  WHERE active = 'false';

UPDATE requests
	SET groupID = 'PUS';

UPDATE exceptions
	SET groupID = 'PUS';

UPDATE drives
	SET groupID = 'PUS';

UPDATE drives
	SET fixed = true
WHERE fixed = 'true';

UPDATE drives
	SET fixed = false
WHERE fixed = 'false';

DELETE FROM drives
WHERE date < date(datetime('now'));

UPDATE rides
	SET groupID = 'PUS';

UPDATE rides
	SET fixed = true
WHERE fixed = 'true';

UPDATE rides
	SET fixed = false
WHERE fixed = 'false';

DELETE FROM rides
WHERE date < date(datetime('now'));
