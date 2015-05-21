from app import app, mysql
from flask import request, jsonify
from shortcuts import *
from MySQLdb import IntegrityError

list_users_query = ("select "+user_fields+" FROM user INNER JOIN forum_authors a"
	" ON user.id = a.author_id"
	" where a.forum_id=")

@app.route('/db/api/forum/listUsers/', methods = ['GET'])
def list_users():
	
	short = request.args.get('forum')
	if short is None:
		return didntFind('forum short name')
	
	since = request.args.get('since_id')	
	order = request.args.get('order')
	limit = request.args.get('limit')
	extra = sinceOrderLimit(since, order, limit, orderby='a.author_id', sinceWhat='a.author_id')	
	if extra == False:
		return badExtra()
	
	
	resp = []
	#conn = mysql.connect()
	cursor = mysql.connection.cursor()
	forum_id = getForumIdByShortname(cursor, short)
	if forum_id is None:
		#cursor.close()
		#conn.close()
		return dontExist('forum')
	
	query = (list_users_query+str(forum_id)+extra+";")
	#query = ("select "+user_fields+" FROM user INNER JOIN"
	#" (select * from forum_authors where forum_authors.forum_id="+str(forum_id)
	#+ extra +") as a ON a.author_id = user.id "+getOrderExtra(order, "a.author_id"))
	
	cursor.execute(query)
	alldata = cursor.fetchall()
	
	for data in alldata:
		subresp = {}
		parseUserData(cursor, subresp, data)
		resp.append(subresp)
		
	#cursor.close()
	#conn.close()
	
	return OK(resp)

@app.route('/db/api/forum/listUsersOld/', methods = ['GET'])
def list_usersOld():
	
	short = request.args.get('forum')
	if short is None:
		return didntFind('forum short name')
	
	since = request.args.get('since_id')	
	order = request.args.get('order')
	limit = request.args.get('limit')
	extra = sinceOrderLimit(since, order, limit, orderby='name', sinceWhat='user.id')	
	if extra == False:
		return badExtra()
	resp = []
	#conn = mysql.connect()
	cursor = mysql.connection.cursor()
	if getUsersResp(resp, cursor, extra, short) == False:
		#cursor.close()
		#conn.close()
		return didntFind('forum')
	#cursor.close()
	#conn.close()
	return OK(resp)

@app.route('/db/api/forum/details/', methods = ['GET'])	
def get_forum_details():
	
	shortname = request.args.get('forum')	
	if shortname is None:
		return didntFind('forum short name')
		
	related = request.args.getlist('related')
	if False == checkRelated(related, ('user')):
		return badJson('"related" parameter is incorrect')
	
	resp = {}
	#conn = mysql.connect()
	cursor = mysql.connection.cursor()
	if False == getForumResp(resp, cursor, short_name=shortname, related=related):
		#cursor.close()
		#conn.close()
		return dontExist('forum')
	#cursor.close()
	#conn.close()
	return OK(resp)

@app.route('/db/api/forum/create/', methods = ['POST'])	
def create_forum():
	
	try:
		shortname = request.json['short_name']
		name = request.json['name']
		email = request.json['user']
		if not areOfType((shortname, name, email), basestring):
			return badTypes()
	except:
		return didntFind('short name, name and user')
	#conn = mysql.connect()
	cursor = mysql.connection.cursor()	
	id = getUserByEmail(email, cursor)
	if id is None:
		#cursor.close()
		#conn.close()
		return dontExist('user')
	resp = {}	
	try:
		query = ("INSERT INTO forum (name, short_name, founder_id)"
		"VALUES(%s, %s, %s);")
		cursor.execute(query, [name, shortname, id])
		mysql.connection.commit()
		resp['id'] = cursor.lastrowid
		resp['short_name'] = shortname
		resp['name'] = name
		resp['user'] = email
	except MySQLdb.IntegrityError:
		id = getForumIdByShortname(cursor, shortname)
		if id is None:
			getForumResp(resp, cursor, name=name)
		else:
			getForumResp(resp, cursor, id=id)
	#cursor.close()
	#conn.close()
	return OK(resp)
