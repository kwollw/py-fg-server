BEGIN TRANSACTION;

CREATE TABLE IF NOT EXISTS "groups" (
	"groupID"	TEXT(5),
	"description"	TEXT(30)
);

INSERT INTO "groups" VALUES ('PUS','Kiel - Eckernförde Schulzentrum');
INSERT INTO "groups" VALUES ('HHG','Kiel - Hohenwestedt Schulen');

UPDATE members
	SET groupID = 'PUS';

UPDATE drives
	SET groupID = 'PUS';

UPDATE exceptions
	SET groupID = 'PUS';

UPDATE requests
	SET groupID = 'PUS';

UPDATE rides
	SET groupID = 'PUS';

COMMIT