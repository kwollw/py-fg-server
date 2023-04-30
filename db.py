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
  password_hash = hashlib.sha1((password + salt).encode()).hexdigest()
  result = db_select('select * from members where (user like ? or mail like ?) and password_sha1 = ?',[user, user, password_hash])
  user = {}
  if len(result) == 1:
    user = result[0]
    del user["password_sha1"]
  return user

def is_uniq_user(groupID, user):
  if groupID and groupID != '':
    result = db_select('select * from members where (groupID, user) = (?,?)',[groupID, user])
  else:
    result = db_select('select * from members where user = ?',[user])
  return len(result) == 0

def groups():
  groups = db_select('select * from groups',[])
  return sorted(groups, key=lambda d: d['description']) 

def active_users(groupID):
  return db_select('select * from members where active = "true" and groupID = ? order by sirname',[groupID])
  
def in_holidays(date):
  result = db_select('select * from holidays where date_from <= ? and date_to >= ?;', [date, date])
  return (len(result) > 0)

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
    #todo: update schedule all weekdays like this
  for exc in requests['selectedExcs']:
    db.execute("DELETE FROM exceptions WHERE exceptionID = ?", [exc['exceptiionID']])
    update_schedule(exc['date'])
  db.commit()

def add_request(request):
  if request['driverStatus'] =='M':
    request['timeToMaxDelay'] = 300
    request['timeFroMaxDelay'] = 300
  if request['weeklyRepeat']:
    #todo: delete all weekdays like this 
    db.execute("DELETE FROM requests WHERE (groupID, user, date) = (?,?,?)",[request['groupID'],request['user'],request['date']])
    db.execute("INSERT INTO requests (groupID, user, date, driver_status, time_to, time_to_max_delay, max_passengers_to, time_fro, time_fro_max_delay, max_passengers_fro) VALUES (?,?,?,?,?,?,?,?,?,?)",[request['groupID'], request['user'], request['date'],request['driverStatus'],request['timeTo'],request['timeToMaxDelay'],request['maxPassengersTo'],request['timeFro'],request['timeFroMaxDelay'],request['maxPassengersFro']])
    #todo: update schedules at all coming weekdays like this 
    update_schedule(request['date'])
  else:
    db.execute("DELETE FROM exceptions WHERE (groupID, user, date) = (?,?,?)",[request['groupID'],request['user'],request['date']])
    db.execute("INSERT INTO exceptions (groupID, user, date, driver_status, time_to, time_to_max_delay, max_passengers_to, time_fro, time_fro_max_delay, max_passengers_fro) VALUES (?,?,?,?,?,?,?,?,?,?)",[request['groupID'], request['user'], request['date'],request['driverStatus'],request['timeTo'],request['timeToMaxDelay'],request['maxPassengersTo'],request['timeFro'],request['timeFroMaxDelay'],request['maxPassengersFro']])
    update_schedule(request['date'])
  db.commit()

def active_requests(groupID, date):
  requests = []
  if (not in_holidays(date)):
    requests = db_select ('select * from requests_view where (groupID, user, date) in (select ?, user, max(date) from requests where date <= ? and strftime("%w",date) = strftime("%w",?) group by groupID, user having (groupID, user) not in (select groupID, user from exceptions where date = ?)) union select * from exceptions_view where date = ? and driver_status != 0;',[groupID, date, date, date, date])
    for d in requests:
      d["date"] = date
  return requests
  
def update_schedule(groupID, date):
  db.execute("delete from drives where not fixed and (groupID, date) = (?,?)", [groupID, date])
  db.execute("delete from rides where not fixed and (groupID, date) = (?,?)", [groupID, date])
  if not in_holidays(date):
    drives = z3.schedule(groupID, date)
    for d in drives:
      db.execute( "INSERT INTO drives (fixed, groupID, Date, Driver, max_passengers_to, max_passengers_fro, time_to, time_fro) VALUES (false,?,?,?,?,?,?,?)", [groupID, d['date'], d['user'], d['max_passengers_to'], d['max_passengers_fro'], d['time_to'], d['time_fro'] ])
      for rider in d['rides_to']:
        db.execute("INSERT INTO rides (fixed, groupID, Date, time, Driver, Rider) VALUES (false, ?, ?, ?, ?, ?)", [groupID, d['date'], d['time_to'], d['user'], rider])
      for rider in d['rides_fro']:
        db.execute("INSERT INTO rides (fixed, groupID, Date, time, Driver, Rider) VALUES (false, ?, ?, ?, ?, ?)", [groupID, d['date'], d['time_fro'], d['user'], rider])
  db.commit()

def schedule(groupID, date):
  print(groupID, date)
  if in_holidays(date):
    update_schedule(groupID, date)
  schedule = db_select("select * from schedule where (groupID, date) = (?,?)", [groupID, date])
  if len(schedule) == 0:
    update_schedule(groupID, date)
    schedule = db_select("select * from schedule where (groupID, date) = (?,?)", [groupID, date])
  print(schedule)
  return schedule

def register(data):
  print(data)
  return ''