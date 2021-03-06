from app import app, mysql
from flask import request, jsonify
from shortcuts import *
from response import *
from MySQLdb import IntegrityError

def forum_list_posts(forum_short, related, since, order, limit):	
	cursor = mysql.connection.cursor()	
	forum_id = getForumIdByShortname(cursor, forum_short)
	if forum_id is None:
		return dontExist('forum')
	
	if 'forum' in related:
		forum = {}
		getForumResp(forum, cursor, forum_id)		
	else:
		forum = forum_short	
	extra = sinceOrderLimit(since, order, limit)
	if extra == False:
		return badExtra()
	resp = []
	
	if getForumPostsResp(resp, cursor, forum_id, extra, related, forum) == False:
		return dontExist('forum')
	
	return OK(resp)

@app.route('/db/api/forum/listPosts/', methods = ['GET'])
def forum_list_posts_view():
	
	
	forum_short = request.args.get('forum')
	if forum_short is None:
		return didntFind('forum shortname')
	related = request.args.getlist('related')
	if False == checkRelated(related, ('thread', 'forum', 'user')):
		return badJson('related argument is incorrect')		
	
		
	since = request.args.get('since')
	limit = request.args.get('limit')
	order = request.args.get('order')
	
	return forum_list_posts(forum_short, related, since, order, limit)


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
	extra = sinceOrderLimit(since, order, limit, orderby='a.name', sinceWhat='a.author_id')	
	if extra == False:
		return badExtra()
	
	
	resp = []
	cursor = mysql.connection.cursor()
	forum_id = getForumIdByShortname(cursor, short)
	if forum_id is None:
		return dontExist('forum')
	
	query = (list_users_query+str(forum_id)+extra+";")

	cursor.execute(query)
	alldata = cursor.fetchall()
	
	for data in alldata:
		subresp = {}
		parseUserData(cursor, subresp, data)
		resp.append(subresp)
		
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
	cursor = mysql.connection.cursor()
	if getUsersResp(resp, cursor, extra, short) == False:
		return didntFind('forum')
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
	cursor = mysql.connection.cursor()
	if False == getForumResp(resp, cursor, short_name=shortname, related=related):
		return dontExist('forum')
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
	cursor = mysql.connection.cursor()	
	id = getUserByEmail(email, cursor)
	if id is None:
		return dontExist('user')
	resp = {}	
	try:
		query = ("INSERT INTO forum (name, short_name, founder_id, founder_email)"
		"VALUES(%s, %s, %s, %s);")
		cursor.execute(query, [name, shortname, id, email])
		mysql.connection.commit()
		resp['id'] = cursor.lastrowid
		resp['short_name'] = shortname
		resp['name'] = name
		resp['user'] = email
	except IntegrityError:
		id = getForumIdByShortname(cursor, shortname)
		if id is None:
			getForumResp(resp, cursor, name=name)
		else:
			getForumResp(resp, cursor, id=id)
	return OK(resp)
