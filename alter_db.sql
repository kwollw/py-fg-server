DROP VIEW drives_count;
DROP VIEW exceptions_view;
DROP VIEW requests_view;
DROP VIEW rides_count;
DROP VIEW schedule;
DROP VIEW total_drives;



CREATE TABLE IF NOT EXISTS "groups" (
	"groupid"	TEXT (5),
	"description"	TEXT (30)
);

CREATE TABLE IF NOT EXISTS "schedule_head" (
	"groupid"	TEXT(5),
	"date"    TEXT(10)
);

CREATE TABLE members2(
	user TEXT (5), 
	groupid TEXT (5),
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
	PRIMARY KEY(user, groupid)
	);

INSERT INTO members2
  SELECT user, groupid, password_sha1, name, sirname, mobile, 
	mail, 0, 0, 0, active, role
	FROM members;

DROP TABLE members;

ALTER TABLE members2 RENAME TO members;

ALTER TABLE drives
	ADD "groupid"	TEXT(5);

ALTER TABLE exceptions
	ADD "groupid"	TEXT(5);

ALTER TABLE requests
	ADD "groupid"	TEXT(5);

ALTER TABLE rides
	ADD "groupid"	TEXT(5);


CREATE VIEW requests_view AS select a.*, rides_count, passengers_count 
from requests a, members b
where a.user = b.user AND a.groupid = b.groupid;

CREATE VIEW exceptions_view AS select a.*, rides_count, passengers_count 
from exceptions a, members b
where a.user = b.user AND a.groupid = b.groupid;

CREATE VIEW drives_count AS SELECT groupid, driver user, count() drives_count FROM rides where date < date(datetime('now')) GROUP BY groupid, driver;

CREATE VIEW rides_count AS SELECT groupid, rider user, count() rides_count FROM rides where date < date(datetime('now')) GROUP BY rider;

CREATE VIEW schedule as 
select d.groupid, d.date, time_to time, 'to' direction, d.driver, d.max_passengers_to max_passengers, count(*) passengers, group_concat(rider, ', ') rider
from drives d left join rides r on (d.groupid = r.groupid and d.driver = r.driver and d.date = r.date and time_to = time)
where time is not NULL
group by d.groupid, d.date, time, direction, d.driver, max_passengers
UNION ALL
select d.groupid, d.date, time_fro time, 'fro' direction, d.driver, d.max_passengers_fro max_passengers, count(*) passengers, group_concat(rider, ', ') rider
from drives d left join rides r on (d.groupid = r.groupid and d.driver = r.driver and d.date = r.date and time_fro = time)
where time is not NULL 
group by d.groupid, d.date, time, direction, d.driver, max_passengers
UNION
select d.groupid, d.date, time_to time, 'to' direction, d.driver, d.max_passengers_to max_passengers, 0 passengers, rider
from drives d left join rides r on (d.groupid = r.groupid and d.driver = r.driver and d.date = r.date and time_to = time)
where rider is NULL and time_to <> ''
group by d.groupid, d.date, time, direction, d.driver, max_passengers
UNION
select d.groupid, d.date, time_fro time, 'fro' direction, d.driver, d.max_passengers_fro max_passengers, 0 passengers, rider
from drives d left join rides r on (d.groupid = r.groupid and d.driver = r.driver and d.date = r.date and time_fro = time)
where rider is NULL and time_fro <> ''
group by d.groupid, d.date, time, direction, d.driver, max_passengers;

CREATE VIEW total_drives AS SELECT groupid, driver user, count(*) drives FROM drives where fixed = true GROUP BY groupid, driver;

CREATE VIEW drive_dates as
select date, groupid, driver as user
from drives
UNION
select date, groupid, rider as user
from rides;
