# Datenbankfunktionen
import sqlite3
import hashlib
from config import salt
import z3solver as z3
from datetime import datetime, timedelta

db = sqlite3.connect('fahrplan.sqlite3')
# db.row_factory = sqlite3.Row

def db_select(query, params):
  cur = db.execute(query, params)
  return [dict((cur.description[i][0], value) for i, value in enumerate(row)) for row in cur.fetchall()]

def getlogin(user, password):
  password_hash = hashlib.sha1((password + salt).encode()).hexdigest()
  result = db_select('SELECT * FROM members WHERE (user LIKE ? OR mail LIKE ?) AND password_sha1 = ?',[user, user, password_hash])
  user = {}
  if len(result) == 1:
    user = result[0]
    del user["password_sha1"]
  return user

def groups():
  groups = db_select('SELECT * FROM groups',[])
  return sorted(groups, key=lambda d: d['description']) 

def active_users(groupid):
  return db_select('SELECT * FROM members WHERE active = true AND groupid = ? ORDER BY sirname',[groupid])
  
def in_holidays(date):
  result = db_select('SELECT * FROM holidays WHERE date_from <= ? AND date_to >= ?;', [date, date])
  return (len(result) > 0)

def update_members():
  c = db_select("SELECT * FROM drives WHERE date < date(datetime('now'))",[])
  if len(c) > 0:
    db.execute("UPDATE members SET passengers_count = (passengers_count + drives_count.drives_count) FROM drives_count WHERE (members.user, members.groupid) = (drives_count.user, drives_count.groupid)")
    db.execute("UPDATE members SET rides_count = (members.rides_count + rides_count.rides_count) FROM rides_count WHERE (members.user, members.groupid) = (rides_count.user, rides_count.groupid)")
    db.execute("UPDATE members SET drives_count = drives_count + total_drives.drives FROM total_drives WHERE (members.user, members.groupid) = (total_drives.user, total_drives.groupid)")
    db.execute("DELETE FROM rides WHERE date < date(datetime('now'))")
    db.execute("DELETE FROM drives WHERE date < date(datetime('now'))")
    db.execute("UPDATE members SET active = false")
    db.execute("UPDATE members SET active = true where (groupid, user) in ( select groupid, user from requests )")
    db.execute("UPDATE members SET active = true where (groupid, user) in ( select groupid, user from exceptions )")
    db.commit()
  
def requests(groupid, user):
  requests = db_select("SELECT * FROM requests WHERE (groupid, user) = (?,?)",[groupid, user])
  return sorted(requests, key=lambda d: d['date']) 

def exceptions(groupid, user):
  db.execute("DELETE FROM exceptions WHERE date < DATE()")
  exceptions = db_select("SELECT * FROM exceptions WHERE (groupid, user) = (?,?)",[groupid, user])
  return sorted(exceptions, key=lambda d: d['date']) 

def delete_requests(requests):
  for req in requests['selectedReqs']:
    db.execute("DELETE FROM requests WHERE requestID = ?", [req['requestID']]) 
    # all weekdays like deleted request
    db.execute("DELETE FROM schedule_head WHERE groupid = ? AND strftime('%w',date) = strftime('%w',?)",[req['groupid'],req['date']])
  for exc in requests['selectedExcs']:
    db.execute("DELETE FROM exceptions WHERE exceptionID = ?", [exc['exceptionID']])
    update_schedules(exc['groupid'], exc['date'])
  db.commit()

def add_request(request):
  print("add request: ", request)
  db.execute("UPDATE members SET active = true where (groupid, user) = (?, ?)",[request['groupid'],request['user']])
  if request['driverStatus'] =='M':
    request['timeToMaxDelay'] = 300
    request['timeFroMaxDelay'] = 300
  if request['weeklyRepeat']:
    db.execute("DELETE FROM drives WHERE groupid = ? AND date > ? AND strftime('%w',date) = strftime('%w',?)", [request['groupid'], request['date'], request['date']])
    db.execute("DELETE FROM rides WHERE groupid = ? AND date > ? AND strftime('%w',date) = strftime('%w',?)", [request['groupid'], request['date'], request['date']])
    db.execute("DELETE FROM requests WHERE (groupid, user, date) = (?,?,?)",[request['groupid'],request['user'],request['date']])
    db.execute("INSERT INTO requests (groupid, user, date, driver_status, time_to, time_to_max_delay, max_passengers_to, time_fro, time_fro_max_delay, max_passengers_fro) VALUES (?,?,?,?,?,?,?,?,?,?)",[request['groupid'], request['user'], request['date'],request['driverStatus'],request['timeTo'],request['timeToMaxDelay'],request['maxPassengersTo'],request['timeFro'],request['timeFroMaxDelay'],request['maxPassengersFro']])
  else:
    db.execute("DELETE FROM exceptions WHERE (groupid, user, date) = (?,?,?)",[request['groupid'],request['user'],request['date']])
    db.execute("INSERT INTO exceptions (groupid, user, date, driver_status, time_to, time_to_max_delay, max_passengers_to, time_fro, time_fro_max_delay, max_passengers_fro) VALUES (?,?,?,?,?,?,?,?,?,?)",[request['groupid'], request['user'], request['date'],request['driverStatus'],request['timeTo'],request['timeToMaxDelay'],request['maxPassengersTo'],request['timeFro'],request['timeFroMaxDelay'],request['maxPassengersFro']])
  update_schedules(request['groupid'], request['date'])
  db.commit()

def active_requests(groupid, date):
  requests = []
  if (not in_holidays(date)):
    requests = db_select ('SELECT * FROM requests_view WHERE (groupid, user, date) in (SELECT ?, user, max(date) FROM requests WHERE date <= ? AND strftime("%w",date) = strftime("%w",?) group by groupid, user having (groupid, user) not in (SELECT groupid, user FROM exceptions WHERE date = date(?))) union SELECT * FROM exceptions_view WHERE date = date(?) AND driver_status != 0;',[groupid, date, date, date, date])
    for d in requests:
      d["date"] = date
  return requests

def next_monday():
  nm = db_select('SELECT date(datetime("now", "localtime", "+36 hours"), "weekday 1") AS date',[])[0]['date']
  return nm

def next_week():
  x = datetime.strptime(next_monday(), '%Y-%m-%d')
  week = []
  for i in range(5):
    week.append(x)
    x += timedelta(days=1)
  return list(map(lambda x: x.strftime('%Y-%m-%d'),week))

def all_groups():
  groups = db_select('select groupid from groups',[])
  return list(map(lambda x: x['groupid'],groups))

def head(groupid, date):
  dow = db_select('SELECT strftime("%w", ?) AS dow',[date])[0]['dow']
  h = db_select('SELECT date FROM schedule_head WHERE groupid = ? AND strftime("%w",date) = strftime("%w",?)',[groupid, date])
  if len(h) == 0:
    db.execute('INSERT INTO schedule_head ("groupid", "date") VALUES (?, date("now", "weekday " || ?))',[groupid, dow])
    h = db_select('SELECT date FROM schedule_head WHERE groupid = ? AND strftime("%w",date) = strftime("%w",?)',[groupid, date])
  return h[0]['date']

# update schedule for specific date
def update_schedule(groupid, date):
  if date >= next_monday(): 
    db.execute("DELETE FROM drives WHERE (groupid, date) = (?,?)", [groupid, date])
    db.execute("DELETE FROM rides WHERE (groupid, date) = (?,?)", [groupid, date])
    if not in_holidays(date):
      drives = z3.schedule(groupid, date)
      for d in drives:
        db.execute( "INSERT INTO drives (fixed, groupid, Date, Driver, max_passengers_to, max_passengers_fro, time_to, time_fro) VALUES (false,?,date(?),?,?,?,?,?)", [groupid, d['date'], d['user'], d['max_passengers_to'], d['max_passengers_fro'], d['time_to'], d['time_fro'] ])
        for rider in d['rides_to']:
          db.execute("INSERT INTO rides (fixed, groupid, Date, time, Driver, Rider) VALUES (false, ?, date(?), ?, ?, ?)", [groupid, d['date'], d['time_to'], d['user'], rider])
        for rider in d['rides_fro']:
          db.execute("INSERT INTO rides (fixed, groupid, Date, time, Driver, Rider) VALUES (false, ?, date(?), ?, ?, ?)", [groupid, d['date'], d['time_fro'], d['user'], rider])
      db.execute("DELETE FROM drives WHERE time_to == '00:00' AND time_fro == '00:00'")
      db.execute("DELETE FROM rides WHERE time == '00:00'")
    db.commit()

# update all schedules from head to date for specific weekday
def update_schedules(groupid, date):
  h = head(groupid, date)
  h = db_select('SELECT date(?,"+7 days") AS date',[h])[0]['date']
  while h < date:
    update_schedule(groupid, h)
    h = db_select('SELECT date(?,"+7 days") AS date',[h])[0]['date']
  update_schedule(groupid, date)
  db.execute('UPDATE schedule_head SET date = ? WHERE groupid = ? AND strftime("%w",date) = strftime("%w",?)',[date, groupid, date])
  db.commit()
  
def finalize_next_week():
  update_members()
  for groupid in all_groups():
    for date in next_week():
      update_schedule(groupid, date)

def schedule(groupid, date):
  if in_holidays(date) or date > head(groupid, date):
    update_schedules(groupid, date)
  schedule = db_select("SELECT * FROM schedule WHERE (groupid, date) = (?,?) and time != '00:00'", [groupid, date])
  return {"Ferien": in_holidays(date), "drives": schedule}

def format_drive(d):
  if d['rider'] != None:
    return f"{d['time']} {d['Driver']} ({d['max_passengers']}) {d['rider']}" 
  else:
    return f"{d['time']} {d['Driver']} ({d['max_passengers']})" 

def schedule2(groupid, user, date):
  if in_holidays(date) or date > head(groupid, date):
    update_schedules(groupid, date)
  schedule = db_select("SELECT time, direction, driver, max_passengers, rider FROM schedule WHERE (groupid, date) = (?,?) and time != '00:00'", [groupid, date])
  myschedule = list(filter(lambda x: x['Driver'] == user or (x['rider'] and any(map(lambda s: s.strip() == user, x['rider'].split(',')))), schedule))
  myto = list(filter(lambda x: x['direction'] == 'to', myschedule))
  myfro = list(filter(lambda x: x['direction'] == 'fro', myschedule))
  other_schedule = list(filter(lambda x: x not in myschedule, schedule))
  otos = list(filter(lambda x: x['direction'] == 'to', other_schedule))
  ofros = list(filter(lambda x: x['direction'] == 'fro', other_schedule))
  return {"date": date, 
          "holiday": in_holidays(date), 
          "myto": '' if len(myto) == 0 else format_drive(myto[0]),
          "myfro": '' if len(myfro) == 0 else format_drive(myfro[0]),
          "otos": list(map(lambda d: format_drive(d),otos)),
          "ofros": list(map(lambda d: format_drive(d),ofros))
          }

def next_days(date, n):
  x = datetime.strptime(date, '%Y-%m-%d')
  week = []
  for i in range(n):
    while x.weekday()>4:
      x += timedelta(days=1)
    week.append(x)
    x += timedelta(days=1)
  return list(map(lambda x: x.strftime('%Y-%m-%d'),week))
    
def schedule_list(groupid, user, date):
  schedule_list = []
  for d in next_days(date, 5):
    schedule_list.append(schedule2(groupid, user, d))
  return schedule_list

def hop_on(groupid, user, date, dir, driver):
  if dir == "to":
    old_ride = db_select("select time FROM rides NATURAL JOIN drives d WHERE time_to = time AND (date, rider) = (?,?)", [date, user])
    new_ride = db_select("select time_to AS time FROM drives WHERE (groupid, date, driver) = (?,?,?)", [groupid, date, driver])
  else:
    old_ride = db_select("select time FROM rides NATURAL JOIN drives d WHERE time_fro = time AND (date, rider) = (?,?)", [date, user])
    new_ride = db_select("select time_fro AS time FROM drives WHERE (groupid, date, driver) = (?,?,?)", [groupid, date, driver])
  # delete old ride if exists:
  if len(old_ride)>0:
    hop_off(groupid, user, date, old_ride[0]['time'])
  # add new ride:
  if len(new_ride)>0:
    db.execute("INSERT INTO rides (groupid, date, time, driver, rider, fixed) VALUES(?,?,?,?,?,true)" , [groupid, date, new_ride[0]['time'], driver, user])
  db.commit()
  return schedule(groupid, date)

def hop_off(groupid, user, date, time):
  db.execute("DELETE FROM rides WHERE (groupid, rider, date, time) = (?,?,?,?)" , [groupid, user, date, time])
  db.commit()
  return schedule(groupid, date)

def register(d):
  password_hash = hashlib.sha1((d['password'] + salt).encode()).hexdigest()
  db.execute("INSERT INTO members (user, groupid, password_sha1, name, sirname, mobile, mail, drives_count, passengers_count, rides_count, active) VALUES (upper(?), ?, ?, ?, ?, ?, ?, 0, 0, 0, true)", [d['user'], d['groupid'], password_hash, d['name'], d['sirname'], d['mobile'], d['mail']])
  db.commit()

def update_user(u):
  if(u['changePassword']):
    password_hash = hashlib.sha1((u['password'] + salt).encode()).hexdigest()
    db.execute("UPDATE members SET password_sha1 = ? WHERE (user,groupid) =(?,?)", [password_hash, u['user'], u['groupid']])
  db.execute("UPDATE members SET (name, sirname, mobile, mail) = (?, ?, ?, ?) WHERE (user,groupid) =(?,?)", [u['name'], u['sirname'], u['mobile'], u['mail'], u['user'], u['groupid']])
 
def next_drive(groupid, user):
  result = db_select("SELECT groupid, user, MIN(date) AS next_drive FROM drive_dates WHERE date >= DATE('now') AND (groupid, user) = (?,?) GROUP BY groupid, user", [groupid, user])
  return (result[0])
