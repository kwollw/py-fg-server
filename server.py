from bottle import *
import jwt
from config import issuer, audience, jwt_config, salt

from bottle_cors_plugin import cors_plugin
import json

import db

app = app()
app.install(cors_plugin('*'))


# Create a restriction on any route with a prefix of '/api/'
# aud=JwtAuth(jwt_config = jwt_config, issuer=issuer, audience=audience, url_prefix='/api/')

# app.install(aud)

@route('/api/users/authenticate', method='POST')
def authenticate():  
  username = request.json.get('username')
  password = request.json.get('password')
  user = db.getlogin(username, password)
  response.content_type = 'application/json'
  if (len(user)>0):
    token = jwt.encode({"user": user["user"]}, jwt_config["key"], algorithm="HS256")
    return json.dumps({ "message":"success", "token":token, "data":user})
  else:
    return json.dumps({ "message":"failed"})

@route('/api/groups', method='GET')
def groups():  
  groups = db.groups()
  response.content_type = 'application/json'
  return json.dumps(groups)

@route('/api/next_drive', method='GET')
def next_drive():  
  groupID = request.params.groupID
  user = request.params.user
  response.content_type = 'application/json'
  return json.dumps(db.next_drive(groupID, user))

@route('/api/users', method='GET')
def users():  
  groupID = request.params.groupID
  userlist = db.active_users(groupID)
  response.content_type = 'application/json'
  return json.dumps(userlist)

@route('/api/requests', method='GET')
def requests():
  groupID = request.params.groupID
  user = request.params.user
  requests = db.requests(groupID, user)
  exceptions = db.exceptions(groupID, user)
  return json.dumps({'requests': requests, 'exceptions': exceptions})

@route('/api/hop_on', method='POST')
def hop_on():
  groupID = request.json.get('groupID')
  date = request.json.get('date')
  user = request.json.get('user')
  date = request.json.get('date')
  dir = request.json.get('dir')
  driver = request.json.get('driver')
  result = db.hop_on(groupID, user, date, dir, driver)
  return json.dumps({'result': result})

@route('/api/hop_off', method='POST')
def hop_off():
  groupID = request.json.get('groupID')
  date = request.json.get('date')
  user = request.json.get('user')
  date = request.json.get('date')
  time = request.json.get('time')
  result = db.hop_off(groupID, user, date, time)
  return json.dumps({'result': result})

@route('/api/schedule', method='POST')
def schedule():
  groupID = request.json.get('groupID')
  date = request.json.get('date')
  result = db.schedule(groupID, date)
  response.content_type = 'application/json'
  return json.dumps(result)

@route('/api/add_request', method='POST')
def add_request():
  result = db.add_request(request.json)
  response.content_type = 'application/json'
  return json.dumps({'message': 'success', 'data': result})

@route('/api/register', method='POST')
def register():
  result = db.register(request.json)
  response.content_type = 'application/json'
  return json.dumps({'message': 'success', 'data': result})

@route('/api/setup', method='POST')
def update_user():
  result = db.update_user(request.json)
  response.content_type = 'application/json'
  return json.dumps({'message': 'success', 'data': result})

@route('/api/delete_requests', method='POST')
def delete_requests():
  result = db.delete_requests(request.json)
  response.content_type = 'application/json'
  return json.dumps({'message': 'success', 'data': result})

app.run(host='localhost', port=4000, debug=True)