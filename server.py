from bottle import *
import jwt
from config import issuer, audience, jwt_config, salt

from bottle_cors_plugin import cors_plugin
import json

import db

install(cors_plugin('*'))


# Create a restriction on any route with a prefix of '/api/'
# aud=JwtAuth(jwt_config = jwt_config, issuer=issuer, audience=audience, url_prefix='/api/')

# app.install(aud)

@route('/api/users/authenticate', method='POST')
def authenticate():  
  user = db.getlogin(request.json['username'], request.json['password'])
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

@route('/api/users', method='GET')
def users():  
  groupID = request.query['group']
  userlist = db.active_users(groupID)
  response.content_type = 'application/json'
  return json.dumps(userlist)

@route('/api/is_user_uniq', method='GET')
def is_uniq_user():  
  groupID = request.query['group']
  user = request.query['user']
  uniq = db.is_uniq_user(groupID, user)
  response.content_type = 'application/json'
  return json.dumps(uniq)

@route('/api/requests', method='GET')
def requests():
  user = request.query['user']
  requests = db.requests(user)
  exceptions = db.exceptions(user)
  return json.dumps({'requests': requests, 'exceptions': exceptions})

@route('/api/schedule', method='POST')
def schedule():
  result = db.schedule(request.json['date'])
  response.content_type = 'application/json'
  return json.dumps(result)

@route('/api/request', method='POST')
def add_request():
  result = db.add_request(request.json)
  response.content_type = 'application/json'
  return json.dumps({'message': 'success', 'data': result})

@route('/api/register', method='POST')
def add_request():
  result = db.register(request.json)
  response.content_type = 'application/json'
  return json.dumps({'message': 'success', 'data': result})

@route('/api/delete_requests', method='POST')
def delete_requests():
  result = db.delete_requests(request.json)
  response.content_type = 'application/json'
  return json.dumps({'message': 'success', 'data': result})

run(host='localhost', port=4000, debug=True)