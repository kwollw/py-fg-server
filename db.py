# Datenbankfunktionen
import sqlite3
import hashlib
from config import salt

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
  
def schedule(date):
  return db_select("select * from schedule where Date = ?", [date])
  