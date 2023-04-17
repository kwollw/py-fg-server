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

def active_users(groupID):
  return db_select('select * from members where active = "true" and groupID = ? order by sirname',[groupID])
  
def in_holidays(date):
  result = db_select('select * from holidays where date_from <= ? and date_to >= ?;', [date, date])
  return (len(result) > 0)

def getactive_requests(date):
  requests = []
  if (not in_holidays(date)):
    requests = db_select ('select * from requests_view where user || date in (select user || max(date) from requests where date <= ? and strftime("%w",date) = strftime("%w",?) group by user having user not in (select user from exceptions where date = ?)) union select * from exceptions_view where date = ? and driver_status != 0;',[date,date,date,date])
    for d in requests:
      d["date"] = date
  return requests
  
def update_schedule(date):
  db.execute("delete from drives where not fixed and date = ?", [date])
  db.execute("delete from rides where not fixed and date = ?", [date])
  if not in_holidays(date):
    drives = z3.schedule(date)
    for d in drives:
      db.execute( "INSERT INTO drives (fixed, Date, Driver, max_passengers_to, max_passengers_fro, time_to, time_fro) VALUES (false,?,?,?,?,?,?)", [d['date'], d['user'], d['max_passengers_to'], d['max_passengers_fro'], d['time_to'], d['time_fro'] ])
      for rider in d['rides_to']:
        db.execute("INSERT INTO rides (fixed, Date, time, Driver, Rider) VALUES (false, ?, ?, ?, ?)", [d['date'], d['time_to'], d['user'], rider])
      for rider in d['rides_fro']:
        db.execute("INSERT INTO rides (fixed, Date, time, Driver, Rider) VALUES (false, ?, ?, ?, ?)", [d['date'], d['time_fro'], d['user'], rider])
  db.commit()

def schedule(date):
  if in_holidays(date):
    update_schedule(date)
  schedule = db_select("select * from schedule where Date = ?", [date])
  print(schedule)
  if len(schedule) == 0:
    print("schedule is empty")
    update_schedule(date)
    schedule = db_select("select * from schedule where Date = ?", [date])
  return schedule
  