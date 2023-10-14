INSERT INTO "groups" VALUES ('PUS','Kiel - Eckernförde Schulzentrum');

UPDATE members
	SET groupID = 'PUS';

UPDATE drives
	SET groupID = 'PUS';

UPDATE drives
	SET fixed = true
WHERE fixed = 'true';

UPDATE drives
	SET fixed = false
WHERE fixed = 'false';

UPDATE exceptions
	SET groupID = 'PUS';

UPDATE requests
	SET groupID = 'PUS';

UPDATE rides
	SET groupID = 'PUS';

UPDATE rides
	SET fixed = true
WHERE fixed = 'true';

UPDATE rides
	SET fixed = false
WHERE fixed = 'false';

UPDATE members
  SET active = true
  WHERE active = 'true';

UPDATE members
  SET active = false
  WHERE active = 'false';
