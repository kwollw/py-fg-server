DROP VIEW drives_count;
DROP VIEW exceptions_view;
DROP VIEW requests_view;
DROP VIEW rides_count;
DROP VIEW schedule;
DROP VIEW total_drives;



CREATE TABLE IF NOT EXISTS "groups" (
	"groupID"	TEXT (5),
	"description"	TEXT (30)
);

CREATE TABLE IF NOT EXISTS "schedule_head" (
	"groupID"	TEXT(5),
	"date"    TEXT(10)
);

CREATE TABLE members2(
	user TEXT (5), 
	groupID TEXT (5),
	password_sha1 TEXT (30) NOT NULL, 
	name TEXT (30), 
	sirname TEXT (30), 
	mobile TEXT (20), 
	mail TEXT (30),
	drives_count INTEGER, 
	passengers_count INTEGER, 
	rides_count INTEGER, 
	active BOOLEAN DEFAULT true, 
	role TEXT DEFAULT "user",
	PRIMARY KEY(user, groupID)
	);
INSERT INTO members2
  SELECT user, groupID, password_sha1, name, sirname, mobile, 
	mail, drives_count, passengers_count, rides_count, active, role
	FROM members;
DROP TABLE members;
ALTER TABLE members2 RENAME TO members;


ALTER TABLE drives
	ADD "groupID"	TEXT(5);

ALTER TABLE exceptions
	ADD "groupID"	TEXT(5);

ALTER TABLE requests
	ADD "groupID"	TEXT(5);

ALTER TABLE rides
	ADD "groupID"	TEXT(5);


CREATE VIEW drives_count AS SELECT groupID, Driver user, count() drives_count FROM rides where fixed = true GROUP BY groupID, Driver;

CREATE VIEW exceptions_view AS select a.*, rides_count, passengers_count 
from exceptions a, members b
where a.user = b.user AND a.groupID = b.groupID;

CREATE VIEW requests_view AS select a.*, rides_count, passengers_count 
from requests a, members b
where a.user = b.user AND a.groupID = b.groupID;

CREATE VIEW rides_count AS SELECT groupID, Rider user, count() rides_count FROM rides where fixed = true GROUP BY Rider;

CREATE VIEW schedule as 
select d.groupID, d.Date, time_to time, 'to' direction, d.Driver, d.max_passengers_to max_passengers, count(*) passengers, group_concat(Rider, ', ') rider, d.fixed
from drives d left join rides r on (d.groupID = r.groupID and d.Driver = r.Driver and d.Date = r.Date and time_to = time)
where time is not NULL
group by d.groupID, d.Date, time, direction, d.Driver, max_passengers
UNION ALL
select d.groupID, d.Date, time_fro time, 'fro' direction, d.Driver, d.max_passengers_fro max_passengers, count(*) passengers, group_concat(Rider, ', ') rider, d.fixed
from drives d left join rides r on (d.groupID = r.groupID and d.Driver = r.Driver and d.Date = r.Date and time_fro = time)
where time is not NULL 
group by d.groupID, d.Date, time, direction, d.Driver, max_passengers
UNION
select d.groupID, d.Date, time_to time, 'to' direction, d.Driver, d.max_passengers_to max_passengers, 0 passengers, rider, d.fixed
from drives d left join rides r on (d.groupID = r.groupID and d.Driver = r.Driver and d.Date = r.Date and time_to = time)
where rider is NULL and time_to <> ''
group by d.groupID, d.Date, time, direction, d.Driver, max_passengers
UNION
select d.groupID, d.Date, time_fro time, 'fro' direction, d.Driver, d.max_passengers_fro max_passengers, 0 passengers, rider, d.fixed
from drives d left join rides r on (d.groupID = r.groupID and d.Driver = r.Driver and d.Date = r.Date and time_fro = time)
where rider is NULL and time_fro <> ''
group by d.groupID, d.Date, time, direction, d.Driver, max_passengers;

CREATE VIEW total_drives AS SELECT groupID, Driver user, count(*) drives FROM drives where fixed = true GROUP BY groupID, Driver;

CREATE VIEW drive_dates as
select date, groupID, driver as user
from drives
UNION
select date, groupID, rider as user
from rides;
