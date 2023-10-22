# Datenbankfunktionen
import sqlite3
import hashlib
from config import salt
import z3solver as z3

db = sqlite3.connect('fahrplan.sqlite3')
# db.row_factory = sqlite3.Row

def db_select(query, params):
  cur = db.execute(query, params)
  return [dict((cur.description[i][0], value) for i, value in enumerate(row)) for row in cur.fetchall()]

def getlogin(user, password):
  password_hash = hashlib.sha1((password + salt).encode(WHERE)).hexdigest()
  result = db_select('SELECT * FROM members WHERE (user LIKE ? OR mail LIKE ?) AND password_sha1 = ?',[user, user, password_hash])
  user = {}
  if len(result) == 1:
    user = result[0]
    del user["password_sha1"]
  return user

def groups():
  groups = db_select('SELECT * FROM groups',[])
  return sorted(groups, key=lambda d: d['description']) 

def active_users(groupID):
  return db_select('SELECT * FROM members WHERE active = true AND groupid = ? ORDER BY sirname',[groupID])
  
def in_holidays(date):
  result = db_select('SELECT * FROM holidays WHERE date_from <= ? AND date_to >= ?;', [date, date])
  return (len(result) > 0)

def update_member_counts():
  sql = "UPDATE members SET passengers_count = passengers_count + (SELECT drives_count FROM drives_count WHERE members.user = drives_count.user)"
  sql = "UPDATE members SET rides_count = rides_count + (SELECT rides_count FROM rides_count WHERE members.user = rides_count.user)"
  sql = "UPDATE members SET drives_count = drives_count + (SELECT drives FROM total_drives WHERE members.user = total_drives.user)"
  sql = "DELETE FROM rides WHERE date < date(datetime('now'))"
  sql = "DELETE FROM drives WHERE date < date(datetime('now'))"
  
def requests(groupID, user):
  requests = db_select("SELECT * FROM requests WHERE (groupID, user) = (?,?)",[groupID, user])
  return sorted(requests, key=lambda d: d['date']) 

def exceptions(groupID, user):
  db.execute("DELETE FROM exceptions WHERE date < DATE()")
  exceptions = db_select("SELECT * FROM exceptions WHERE (groupID, user) = (?,?)",[groupID, user])
  return sorted(exceptions, key=lambda d: d['date']) 

def delete_requests(requests):
  for req in requests['selectedReqs']:
    db.execute("DELETE FROM requests WHERE requestID = ?", [req['requestID']]) 
    # all weekdays like deleted request
    db.execute("DELETE FROM schedule_head WHERE groupID = ? AND strftime('%w',date) = strftime('%w',?)",[req['groupID'],req['date']])
  for exc in requests['selectedExcs']:
    db.execute("DELETE FROM exceptions WHERE exceptionID = ?", [exc['exceptionID']])
    update_schedules(exc['groupID'], exc['date'])
  db.commit()

def add_request(request):
  if request['driverStatus'] =='M':
    request['timeToMaxDelay'] = 300
    request['timeFroMaxDelay'] = 300
  if request['weeklyRepeat']:
    db.execute("DELETE FROM drives WHERE groupID = ? AND date > ? AND strftime('%w',date) = strftime('%w',?)", [request['groupID'], request['date'], request['date']])
    db.execute("DELETE FROM rides WHERE groupID = ? AND date > ? AND strftime('%w',date) = strftime('%w',?)", [request['groupID'], request['date'], request['date']])
    db.execute("DELETE FROM requests WHERE (groupID, user, date) = (?,?,?)",[request['groupID'],request['user'],request['date']])
    db.execute("INSERT INTO requests (groupID, user, date, driver_status, time_to, time_to_max_delay, max_passengers_to, time_fro, time_fro_max_delay, max_passengers_fro) VALUES (?,?,?,?,?,?,?,?,?,?)",[request['groupID'], request['user'], request['date'],request['driverStatus'],request['timeTo'],request['timeToMaxDelay'],request['maxPassengersTo'],request['timeFro'],request['timeFroMaxDelay'],request['maxPassengersFro']])
  else:
    db.execute("DELETE FROM exceptions WHERE (groupID, user, date) = (?,?,?)",[request['groupID'],request['user'],request['date']])
    db.execute("INSERT INTO exceptions (groupID, user, date, driver_status, time_to, time_to_max_delay, max_passengers_to, time_fro, time_fro_max_delay, max_passengers_fro) VALUES (?,?,?,?,?,?,?,?,?,?)",[request['groupID'], request['user'], request['date'],request['driverStatus'],request['timeTo'],request['timeToMaxDelay'],request['maxPassengersTo'],request['timeFro'],request['timeFroMaxDelay'],request['maxPassengersFro']])
  update_schedules(request['groupID'], request['date'])
  db.commit()

def active_requests(groupID, date):
  requests = []
  if (not in_holidays(date)):
    requests = db_select ('SELECT * FROM requests_view WHERE (groupID, user, date) in (SELECT ?, user, max(date) FROM requests WHERE date <= ? AND strftime("%w",date) = strftime("%w",?) group by groupID, user having (groupID, user) not in (SELECT groupID, user FROM exceptions WHERE date = date(?))) union SELECT * FROM exceptions_view WHERE date = date(?) AND driver_status != 0;',[groupID, date, date, date, date])
    for d in requests:
      d["date"] = date
  return requests

def next_monday():
  nm = db_select('SELECT date(datetime("now", "localtime", "+36 hours"), "weekday 1") AS date',[])[0]['date']
  return nm

def head(groupID, date):
  dow = db_select('SELECT strftime("%w", ?) AS dow',[date])[0]['dow']
  h = db_select('SELECT date FROM schedule_head WHERE groupID = ? AND strftime("%w",date) = strftime("%w",?)',[groupID, date])
  if len(h) == 0:
    db.execute('INSERT INTO schedule_head ("groupID", "date") VALUES (?, date("now", "weekday " || ?))',[groupID, dow])
    h = db_select('SELECT date FROM schedule_head WHERE groupID = ? AND strftime("%w",date) = strftime("%w",?)',[groupID, date])
  return h[0]['date']

# update schedule for specific date
def update_schedule(groupID, date):
  if date >= next_monday(): 
    db.execute("DELETE FROM drives WHERE (groupID, date) = (?,?)", [groupID, date])
    db.execute("DELETE FROM rides WHERE (groupID, date) = (?,?)", [groupID, date])
    if not in_holidays(date):
      drives = z3.schedule(groupID, date)
      for d in drives:
        db.execute( "INSERT INTO drives (fixed, groupID, Date, Driver, max_passengers_to, max_passengers_fro, time_to, time_fro) VALUES (false,?,date(?),?,?,?,?,?)", [groupID, d['date'], d['user'], d['max_passengers_to'], d['max_passengers_fro'], d['time_to'], d['time_fro'] ])
        for rider in d['rides_to']:
          db.execute("INSERT INTO rides (fixed, groupID, Date, time, Driver, Rider) VALUES (false, ?, date(?), ?, ?, ?)", [groupID, d['date'], d['time_to'], d['user'], rider])
        for rider in d['rides_fro']:
          db.execute("INSERT INTO rides (fixed, groupID, Date, time, Driver, Rider) VALUES (false, ?, date(?), ?, ?, ?)", [groupID, d['date'], d['time_fro'], d['user'], rider])
    db.commit()

# update all schedules from head to date for specific weekday
def update_schedules(groupID, date):
  h = head(groupID, date)
  h = db_select('SELECT date(?,"+7 days") AS date',[h])[0]['date']
  while h < date:
    update_schedule(groupID, h)
    h = db_select('SELECT date(?,"+7 days") AS date',[h])[0]['date']
  update_schedule(groupID, date)
  db.execute('UPDATE schedule_head SET date = ? WHERE groupID = ? AND strftime("%w",date) = strftime("%w",?)',[date, groupID, date])
  db.commit()
  
def schedule(groupID, date):
  if in_holidays(date) or date > head(groupID, date):
    update_schedules(groupID, date)
  schedule = db_select("SELECT * FROM schedule WHERE (groupID, date) = (?,?)", [groupID, date])
  return {"Ferien": in_holidays(date), "drives": schedule}

def hop_on(groupID, user, date, dir, driver):
  if dir == "to":
    old_ride = db_select("select time FROM rides NATURAL JOIN drives d WHERE time_to = time AND (date, rider) = (?,?)", [date, user])
    new_ride = db_select("select time_to AS time FROM drives WHERE (groupID, date, driver) = (?,?,?)", [groupID, date, driver])
  else:
    old_ride = db_select("select time FROM rides NATURAL JOIN drives d WHERE time_fro = time AND (date, rider) = (?,?)", [date, user])
    new_ride = db_select("select time_fro AS time FROM drives WHERE (groupID, date, driver) = (?,?,?)", [groupID, date, driver])
  # delete old ride if exists:
  if len(old_ride)>0:
    hop_off(groupID, user, date, old_ride[0]['time'])
  # add new ride:
  if len(new_ride)>0:
    db.execute("INSERT INTO rides (groupid, date, time, driver, rider, fixed) VALUES(?,?,?,?,?,true)" , [groupID, date, new_ride[0]['time'], driver, user])
  db.commit()
  return schedule(groupID, date)

def hop_off(groupID, user, date, time):
  db.execute("DELETE FROM rides WHERE (groupID, rider, date, time) = (?,?,?,?)" , [groupID, user, date, time])
  db.commit()
  return schedule(groupID, date)

def register(d):
  print(d)
  password_hash = hashlib.sha1((d['password'] + salt).encode()).hexdigest()
  db.execute("INSERT INTO members (user, groupID, password_sha1, name, sirname, mobile, mail, drives_count, passengers_count, rides_count, active) VALUES (upper(?), ?, ?, ?, ?, ?, ?, 0, 0, 0, true)", [d['user'], d['groupID'], password_hash, d['name'], d['sirname'], d['mobile'], d['mail']])
  db.commit()

def update_user(u):
  print(u)
  if(u['changePassword']):
    password_hash = hashlib.sha1((u['password'] + salt).encode()).hexdigest()
    db.execute("UPDATE members SET password_sha1 = ? WHERE (user,groupID) =(?,?)", [password_hash, u['user'], u['groupID']])
  db.execute("UPDATE members SET (name, sirname, mobile, mail) = (?, ?, ?, ?) WHERE (user,groupID) =(?,?)", [u['name'], u['sirname'], u['mobile'], u['mail'], u['user'], u['groupID']])
 
def next_drive(groupID, user):
  result = db_select("SELECT groupid, user, MIN(date) AS next_drive FROM drive_dates WHERE date >= DATE('now') AND (groupID, user) = (?,?) GROUP BY groupID, user", [groupID, user])
  return (result[0])
