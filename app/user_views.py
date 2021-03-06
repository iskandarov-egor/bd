from app import app, mysql
from flask import request, jsonify
import MySQLdb
import ujson
from response import *
from shortcuts import *
	

@app.route('/db/api/user/listPosts/', methods = ['GET'])
def user_list_posts_view():
	
	user_email = request.args.get('user')
	if user_email is None:
		return didntFind('user email')
	cursor = mysql.connection.cursor()	
	
	since = request.args.get('since')
	limit = request.args.get('limit')
	order = request.args.get('order')
	
	extra = sinceOrderLimit(since, order, limit)
	if extra == False:
		return badExtra()
	resp = []
	if getUserPostsResp(resp, cursor, user_email, extra) == False:
		return dontExist('user')
		
	
	return OK(resp)	
	

@app.route('/db/api/user/listPostsQW/', methods = ['GET'])
def list_postsQW():
	user_email = request.args.get('user')
	if user_email is None:
		return didntFind('user email')
	
	since = request.args.get('since')
	limit = request.args.get('limit')
	order = request.args.get('order')
	
	extra = sinceOrderLimit(since, order, limit)
	if extra == False:
		return badExtra()
	resp = []
	cursor = mysql.connection.cursor()
	
	query = "SELECT "+post_fields+" FROM post WHERE matpath=%s "+extra+";";
	cursor.execute(query, [user_email])
	
	return OK(resp)
	
@app.route('/db/api/user/create/', methods = ['POST'])	
def create_user():
	try:
		username = request.json['username']
		name = request.json['name']
		about = request.json['about']
		email = request.json['email']
	except:
		return didntFind()
	if not(areOfType((username, name, about, email), basestring)):
		
		return wrongTypes()
	isAnonymous = False
	if 'isAnonymous' in request.json:
		isAnonymous = request.json['isAnonymous']
		if type(isAnonymous) is not bool:
			return wrongTypes()
	cursor = mysql.connection.cursor()
	try:
		
		query = ("INSERT INTO user (username, about, name, email, isAnonymous)"
		"VALUES(%s, %s, %s, %s, %s);")
		cursor.execute(query, [username, about, name, email, isAnonymous])
		mysql.connection.commit()
		resp = {}
		resp['about'] = about
		resp['email'] = email
		resp['id'] = cursor.lastrowid
		resp['isAnonymous'] = isAnonymous
		resp['name'] = name
		resp['username'] = username
		
		return OK(resp)
	except MySQLdb.IntegrityError as err:
		tosend = {}
		tosend['code'] = 5
		tosend['response'] = 'user with this email already exists'	
		return ujson.dumps(tosend)
	
	
@app.route('/db/api/user/details/', methods = ['GET'])	
def get_user_details():
	tosend = {}
	email = request.args.get('user')	
	if email is None:
		didntFind('user email')
	
	resp = {}
	cursor = mysql.connection.cursor()
	if False == getUserResp(resp, cursor, email):
		return dontExist('user')	
	tosend['code'] = 0
	tosend['response'] = resp
	return ujson.dumps(tosend)
	


@app.route('/db/api/user/listFollowing/', methods = ['GET'])		
@app.route('/db/api/user/listFollowers/', methods = ['GET'])
def list_followers_ees():
	tosend = {}
	email = request.args.get('user')
	if email is None:
		return didntFind('user email')
	
	resp = []
	cursor = mysql.connection.cursor()
	id = getUserByEmail(email, cursor)
	if id is None:
		return dontExist('user')
	
	since = request.args.get('since_id')
	order = request.args.get('order')
	limit = request.args.get('limit')
	
	extra = sinceOrderLimit(since, order, limit, orderby='name', sinceWhat='id')	
	
	if request.url_rule.rule == '/db/api/user/listFollowers/':
		getFollowersResp(cursor, id, resp, False, extra)
	else:
		getFollowersResp(cursor, id, resp, True, extra)	
	tosend['code'] = 0
	tosend['response'] = resp	
			
	return ujson.dumps(tosend)

@app.route('/db/api/user/follow/', methods = ['POST'])
@app.route('/db/api/user/unfollow/', methods = ['POST'])	
def un_follow_user():
	tosend = {}	
	isFollow = (request.url_rule.rule == '/db/api/user/follow/')
	if not('follower' in request.json and 'followee' in request.json ):
		return didntFind('follower or followee')
	
	follower_email = request.json['follower']
	followee_email = request.json['followee']
	
	if not areOfType((follower_email, followee_email), basestring):
		return wrongTypes()
	
	resp = {}
	cursor = mysql.connection.cursor()
	follower_id = getUserByEmail(follower_email, cursor)
	followee_id = getUserByEmail(followee_email, cursor)
	if follower_id is None:
		return dontExist('follower')
	if followee_id is None:
		return dontExist('followee')
		
	if isFollow:
		query = ("INSERT IGNORE INTO following (follower_id, followee_id) "
				"VALUES(%s, %s);")
	else:
		query = "DELETE FROM following WHERE follower_id = %s AND followee_id = %s"		
	cursor.execute(query, [follower_id, followee_id])		
	mysql.connection.commit()	
	
	getUserResp(resp, cursor, id=follower_id)
	tosend['code'] = 0
	tosend['response'] = resp
				
	return ujson.dumps(tosend)		

@app.route('/db/api/user/updateProfile/', methods = ['POST'])	
def update_profile():
	tosend = {}	
	try:
		email = request.json['user']
		name = 	request.json['name']
		about = request.json['about']
	except:
		return didntFind()
	
	if not (areOfType((email, name, about), basestring)):
		return wrongTypes()
	resp = {}
	cursor = mysql.connection.cursor()
	id = getUserByEmail(email, cursor)
	if id is None:
		return dontExist('user')
	
	query = ("UPDATE user "
			 "SET name = %s, about = %s "
			 "WHERE id = ")
	query += str(id)
	query += ';'			
	cursor.execute(query, [name, about])
	mysql.connection.commit()
	
	getUserResp(resp, cursor, id = id)
	return OK(resp)


@app.route('/db/api/clear/', methods = ['POST'])	
def clear():
	if app.config['MYSQL_DB'] == 'forumdb0' or app.config['MYSQL_DB'] == 'forumdb3' or app.config['MYSQL_DB'] == 'forumdb2':
		shutdown_server()
		return "NO"
	cursor = mysql.connection.cursor()
	cursor.execute("DELETE FROM forum_authors;")
	cursor.execute("DELETE FROM subscription;")
	cursor.execute("DELETE FROM following;")
	cursor.execute("DELETE FROM post;")
	cursor.execute("DELETE FROM thread;")
	cursor.execute("DELETE FROM forum;")
	cursor.execute("DELETE FROM user;")
	mysql.connection.commit()
	tosend = {}
	tosend['code'] = 0
	tosend['response'] = "OK"
	return ujson.dumps(tosend)
	
def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()

@app.route('/db/api/status/', methods = ['GET'])	
def status():
	resp = {}
	cursor = mysql.connection.cursor()
	getStatus(resp, cursor, 'user')
	getStatus(resp, cursor, 'forum')
	getStatus(resp, cursor, 'thread')
	getStatus(resp, cursor, 'post')
	tosend = { 'code' : 0, 'response' : resp }
	return jsonify(**tosend)

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
	tosend = {}
	tosend['code'] = 3
	tosend['response'] = "this url is not in api"
	return jsonify(**tosend)
	
