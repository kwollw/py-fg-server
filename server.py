from bottle import Bottle
from JwtAuth import JwtAuth
from config import issuer, audience

from bottle.ext import sqlite
from bottle_cors_plugin import cors_plugin
import json

app = Bottle()
# Create a restriction on any route with a prefix of '/api/'
aud=JwtAuth(jwt_config={issuer=issuer, audience=audience, url_prefix='/api/')

app.install(sqlite.Plugin(dbfile='fahrplan.sqlite3'))
app.install(cors_plugin('*'))

@app.route('/api2/users', method='GET')
def users(db):  
  cur = db.execute('select * from members where active = "true" order by sirname')
  result = [dict((cur.description[i][0], value) for i, value in enumerate(row)) for row in cur.fetchall()]
  response.content_type = 'application/json'
  return json.dumps({'message': 'success', 'users': result})

@app.route('/api2/schedule', method='POST')
def schedule(db):  
  data = request.json
  cur = db.execute("select * from schedule where Date = :date", data)
  result = [dict((cur.description[i][0], value) for i, value in enumerate(row)) for row in cur.fetchall()]
  response.content_type = 'application/json'
  return json.dumps({'message': 'success', 'data': result})

app.run(host='localhost', port=4001, debug=True)