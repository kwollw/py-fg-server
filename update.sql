INSERT INTO "groups" VALUES ('PUS','Kiel - Eckernförde Schulzentrum');

UPDATE members
	SET groupid = 'PUS';

UPDATE members
  SET active = true
  WHERE active = 'true';

UPDATE members
  SET active = false
  WHERE active = 'false';

UPDATE requests
	SET groupid = 'PUS';

UPDATE exceptions
	SET groupid = 'PUS';

UPDATE drives
	SET groupid = 'PUS';

UPDATE drives
	SET fixed = true
WHERE fixed = 'true';

UPDATE drives
	SET fixed = false
WHERE fixed = 'false';

UPDATE rides
	SET groupid = 'PUS';

UPDATE rides
	SET fixed = true
WHERE fixed = 'true';

UPDATE rides
	SET fixed = false
WHERE fixed = 'false';
