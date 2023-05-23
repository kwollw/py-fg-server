BEGIN TRANSACTION;
CREATE TABLE  IF NOT EXISTS "groups" (
	"groupID"	TEXT (5),
	"description"	TEXT (30)
);

ALTER TABLE drives
	ADD "groupID"	TEXT(5);

ALTER TABLE exceptions
	ADD "groupID"	TEXT(5);

ALTER TABLE requests
	ADD "groupID"	TEXT(5);


ALTER TABLE rides
	ADD "groupID"	TEXT(5);

DROP VIEW drives_count;
CREATE VIEW drives_count AS SELECT groupID, Driver user, count() drives_count FROM rides where fixed = 'true' GROUP BY groupID, Driver;

DROP VIEW exceptions_view;
CREATE VIEW exceptions_view AS select a.*, rides_count, passengers_count 
from exceptions a, members b
where a.user = b.user;

DROP VIEW requests_view;
CREATE VIEW requests_view AS select a.*, rides_count, passengers_count 
from requests a, members b
where a.user = b.user;

DROP VIEW rides_count;
CREATE VIEW rides_count AS SELECT groupID, Rider user, count() rides_count FROM rides where fixed = true GROUP BY Rider;

DROP VIEW schedule;
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

DROP VIEW total_drives;
CREATE VIEW total_drives AS SELECT groupID, Driver user, count(*) drives FROM drives where fixed = true GROUP BY groupID, Driver;

CREATE VIEW drive_dates as
select date, groupID, driver as user
from drives
UNION
select date, groupID, rider as user
from rides;

COMMIT;
