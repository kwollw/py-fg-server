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

@route('/api/users', method='GET')
def users():  
  groupID = "PUS" # to be parameterized
  userlist = db.active_users(groupID)
  response.content_type = 'application/json'
  return json.dumps({'message': 'success', 'users': userlist})

@route('/api/schedule', method='POST')
def schedule():
  result = db.schedule(request.json['date'])
  response.content_type = 'application/json'
  return json.dumps({'message': 'success', 'data': result})

@route('/requests', method='GET')
def requests():
  result = db.requests(request.json['user'])
  return json.dumps({'message': 'success', 'requests': result})

@route('/request', method='POST')
def add_request()
  print("to be implemented")
  result = db.add_request(request.json['data'])
  response.content_type = 'application/json'
  return json.dumps({'message': 'success', 'data': result})



run(host='localhost', port=4000, debug=True)