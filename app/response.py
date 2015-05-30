import ujson
from Flask import jsonify

def dontExist(what):
	tosend = {}
	tosend['code'] = 1	
	tosend['response'] = what + " doesn't exist"
	return jsonify(**tosend)

def badJson(err):
	tosend = {}
	tosend['code'] = 3	
	tosend['response'] = err
	return jsonify(**tosend)

def OK(resp):
	tosend = {}
	tosend['code'] = 0
	tosend['response'] = resp
	return ujson.dumps(tosend)

def didntFind(what = None):
	tosend = {}
	tosend['code'] = 2
	if what is None:
		tosend['response'] = "couldn't find some required fields"
	else:	
		tosend['response'] = what + " required"
	return jsonify(**tosend)

def badTypes():
	return badJson('argument types are incorrect')

def badExtra():
	return badJson('since, order or limit are incorrect')

def wrongTypes():
	return badJson('incorrect argument types')
