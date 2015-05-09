from app import app, mysql
from flask import request, jsonify
import MySQLdb
from shortcuts import *

@app.route('/db/api/post/vote/', methods = ['POST'])	
def vote_post():
	
	try:
		id = request.json['post']
		vote = request.json['vote']
		if type(id) != int:
			return badTypes()
	except:
		return didntFind('post id and vote')
	
	if vote == 1:
		query = "UPDATE post SET likes = likes + 1 WHERE id = %s"
	elif vote == -1:
		query = "UPDATE post SET dislikes = dislikes + 1 WHERE id = %s"
	else:
		return badJson('vote must be 1 or -1')
	
	conn = mysql.connect()
	cursor = conn.cursor()
	cursor.execute("SELECT id FROM post WHERE id = %s;", id)
	if cursor.fetchone() is None:
		cursor.close()
		conn.close()
		return dontExist('post')
	
	cursor.execute(query, (id))
	conn.commit()
	resp = {}
	
	getPostRespById(resp, cursor, id)
	cursor.close()
	conn.close()
	return OK(resp)

@app.route('/db/api/post/update/', methods = ['POST'])	
def update_post():
	
	try:
		id = request.json['post']
		message = request.json['message']
		if not(type(id)==int and isinstance(message, basestring)):
			return badTypes()
	except:
		return didntFind('post id and message')

	resp = {}
	conn = mysql.connect()
	cursor = conn.cursor()
	cursor.execute("SELECT id FROM post WHERE id = %s;", id)
	if cursor.fetchone() is None:
		cursor.close()
		conn.close()
		return dontExist('post')
	
	query = "UPDATE post SET message = %s WHERE id = %s"
		
	cursor.execute(query, (message, id))
	conn.commit()
	resp = {}
	
	getPostRespById(resp, cursor, id)
	cursor.close()
	conn.close()
	return OK(resp)


@app.route('/db/api/post/remove/', methods = ['POST'])
@app.route('/db/api/post/restore/', methods = ['POST'])	
def restmove_post():
	try:
		id = request.json['post']
		if type(id) != int:
			return badTypes()
	except:
		return didntFind('post id')	
	
	resp = {}

	if request.url_rule.rule == '/db/api/post/remove/':
		query = "UPDATE post SET isDeleted = TRUE WHERE id = %s"
	else:	
		query = "UPDATE post SET isDeleted = FALSE WHERE id = %s"
	conn = mysql.connect()
	cursor = conn.cursor()	
	cursor.execute(query, (id))
	conn.commit()
	resp = {}
	resp['post'] = id
	cursor.close()
	conn.close()
	return OK(resp)	


@app.route('/db/api/post/list/', methods = ['GET'])	
@app.route('/db/api/forum/listPosts/', methods = ['GET'])
@app.route('/db/api/user/listPosts/', methods = ['GET'])
def list_posts():
	fromforum = (request.url_rule.rule == '/db/api/forum/listPosts/')
	if fromforum == False:
		fromuser = (request.url_rule.rule == '/db/api/user/listPosts/')
	else:
		fromuser = False	

	if fromuser:
		user_email = request.args.get('user')
		if user_email is None:
			return didntFind('user email')
	else:
		user_email = None
	forum_short = request.args.get('forum')
	if forum_short is None and not fromuser:
		if fromforum:
			return didntFind('forum shortname')
		thread_id = request.args.get('thread')
		if thread_id is None:
			return didntFind('forum shortname or post id')
	else:
		thread_id = None
		
	if fromforum:
		related = request.args.getlist('related')
		if False == checkRelated(related, ('thread', 'forum', 'user')):
			return badJson('related argument is incorrect')
	else:
		related = []
	
	since = request.args.get('since')
	limit = request.args.get('limit')
	order = request.args.get('order')
	
	extra = sinceOrderLimit(since, order, limit)
	if extra == False:
		return badExtra()
	resp = []
	conn = mysql.connect()
	cursor = conn.cursor()
	if getPostsResp(resp, cursor, forum_short, thread_id, user_email, extra, related) == False:
		cursor.close()
		conn.close()
		if fromforum:
			return dontExist('forum')
		elif fromuser:
			return dontExist('user')
		else:
			return dontExist('thread')
	cursor.close()
	conn.close()
	return OK(resp)

@app.route('/db/api/post/create/', methods = ['POST'])
def create_post():
	try:
		date = request.json['date']
		thread_id = request.json['thread']
		message = request.json['message']
		user_email = request.json['user']
		forum_short = request.json['forum']
		if not(areOfType((message, date), basestring) and type(thread_id)==int):
			return badTypes()
	except:	
		return didntFind()
	try:
		parent_id = request.json['parent']
		if type(parent_id) != int and parent_id is not None:
			return badTypes()
	except:
		parent_id = None
	isApproved = jsonOrFalse(request.json, 'isApproved')
	isHighlighted = jsonOrFalse(request.json, 'isHighlighted')
	isEdited = jsonOrFalse(request.json, 'isEdited')
	isDeleted = jsonOrFalse(request.json, 'isDeleted')
	isSpam = jsonOrFalse(request.json, 'isSpam')
	if not(areOfType((isApproved, isHighlighted, isEdited, isDeleted, isSpam), bool)):		
		return badTypes()
	
	conn = mysql.connect()
	cursor = conn.cursor()
	forum_id = getForumIdByShortname(cursor, forum_short)
	if forum_id is None:
		cursor.close()
		conn.close()
		return dontExist('forum')
	thread_forum = getForumByThread(cursor, thread_id)
	if thread_forum is None:
		cursor.close()
		conn.close()
		return dontExist('thread')
	if thread_forum != forum_id:
		cursor.close()
		conn.close()
		return badJson('thread is not in specified forum')
		
	author_id = getUserByEmail(user_email, cursor)
	if author_id is None:
		cursor.close()
		conn.close()
		return dontExist('user')
	
	if parent_id is None:
		path = ''
		isroot=True
	else:	
		path = getParentMatpath(cursor, parent_id)
		isroot = False
	query = ("INSERT INTO post (forum_id, message, author_id"
			", isApproved, isHighlighted, isDeleted, isEdited, isSpam"
			", date, thread_id, isRoot) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);")
	cursor.execute(query, (forum_id, message, author_id, \
		isApproved, isHighlighted, isDeleted, isEdited, isSpam , date, thread_id, isroot))
	conn.commit()
	row = cursor.lastrowid
	
	cursor.execute("UPDATE post SET matpath='"+path+getPathPiece(row)+"' WHERE id="+str(row)+';')
	conn.commit()
	cursor.close()
	conn.close()
	resp = {}
	resp['date'] = date
	resp['forum'] = forum_short
	resp['id'] = row
	resp['isApproved'] = isApproved
	resp['isEdited'] = isEdited
	resp['isHighlighted'] = isHighlighted
	resp['isSpam'] = isSpam
	resp['message'] = message
	resp['parent'] = 'NULL'
	resp['thread'] = thread_id
	resp['user'] = user_email

	return OK(resp)

@app.route('/db/api/post/details/', methods = ['GET'])	
def post_details():
	id = request.args.get('post')
	if id is None:
		return didntFind('post')
	
	related = request.args.getlist('related')
	resp = {}
	conn = mysql.connect()
	cursor = conn.cursor()
	if getPostRespById(resp, cursor, id, related) == False:
		cursor.close()
		conn.close()
		return dontExist('post')
	cursor.close()
	conn.close()	
	return OK(resp)

