from bottle import *
import jwt
from config import issuer, audience, jwt_config, salt

import sqlite3

from bottle_cors_plugin import cors_plugin
import json
import hashlib

db = sqlite3.connect('fahrplan.sqlite3')
db.row_factory = sqlite3.Row

install(cors_plugin('*'))


# Create a restriction on any route with a prefix of '/api/'
# aud=JwtAuth(jwt_config = jwt_config, issuer=issuer, audience=audience, url_prefix='/api/')

# app.install(aud)

@route('/api/users/authenticate', method='POST')
def authenticate():  
  user = request.json['username']
  password = hashlib.sha1((request.json['password'] + salt).encode()).hexdigest()
  print(user, password)
  cur = db.execute('select * from members where (user like ? or mail like ?) and password_sha1 = ?',[user, user, password])
  valid_user = cur.fetchall()
  if len(valid_user) == 1:
    print('successful login for ', valid_user[0]['user'], valid_user[0]['name'], valid_user[0]['groupID'])
    token = jwt.encode({"some": "payload"}, jwt_config["key"], algorithm="HS256")
    response.headers['Content-Type'] = 'application/json'
    return json.dumps({ "message":"success","token":token, "data":valid_user[0]['name']})
  else:
    print('login failed')
    response.headers['Content-Type'] = 'application/json'
    return json.dumps({ "message":"failed"})


@route('/api/users', method='GET')
def users():  
  cur = db.execute('select * from members where active = "true" order by sirname')
  result = [dict((cur.description[i][0], value) for i, value in enumerate(row)) for row in cur.fetchall()]
  response.content_type = 'application/json'
  return json.dumps({'message': 'success', 'users': result})

@route('/api/schedule', method='POST')
def schedule():  
  data = request.json
  cur = db.execute("select * from schedule where Date = :date", data)
  result = [dict((cur.description[i][0], value) for i, value in enumerate(row)) for row in cur.fetchall()]
  response.content_type = 'application/json'
  return json.dumps({'message': 'success', 'data': result})

run(host='localhost', port=4000, debug=True)