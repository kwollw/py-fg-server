from bottle import route, run

@route('/api2/hello')
def hello():
    return "Hello World!"

run(host='localhost', port=4001, debug=True)