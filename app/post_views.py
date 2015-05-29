from app import app, mysql
from flask import request, jsonify
import MySQLdb
from forum_views import forum_list_posts
from shortcuts import *
from response import *
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
	
	cursor = mysql.connection.cursor()
	cursor.execute("SELECT id FROM post WHERE id = %s;", [id])
	if cursor.fetchone() is None:
		return dontExist('post')
	
	cursor.execute(query, [id])
	mysql.connection.commit()
	resp = {}
	
	getPostRespById(resp, cursor, id)
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
	cursor = mysql.connection.cursor()
	cursor.execute("SELECT id FROM post WHERE id = %s;", [id])
	if cursor.fetchone() is None:
		return dontExist('post')
	
	query = "UPDATE post SET message = %s WHERE id = %s"
		
	cursor.execute(query, [message, id])
	mysql.connection.commit()
	resp = {}
	
	getPostRespById(resp, cursor, id)
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
	cursor = mysql.connection.cursor()	
	cursor.execute(query, [id])
	mysql.connection.commit()
	resp = {}
	resp['post'] = id
	return OK(resp)	



@app.route('/db/api/post/list/', methods = ['GET'])	
def list_posts():
	
	known = {}
	
	forum_short = request.args.get('forum')
	if forum_short is None:
		thread_id = request.args.get('thread')
		if thread_id is None:
			return didntFind('forum shortname or post id')
	else:
		thread_id = None
	
	since = request.args.get('since')
	limit = request.args.get('limit')
	order = request.args.get('order')
	
	if forum_short is not None:
		return forum_list_posts(forum_short, [], since, order, limit)
	
	cursor = mysql.connection.cursor()	
	extra = sinceOrderLimit(since, order, limit)
	if extra == False:
		return badExtra()
	resp = []
	
	if getThreadPostsResp(resp, cursor, thread_id, extra) == False:
		return dontExist('thread')
	
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
	
	cursor = mysql.connection.cursor()
	forum_id = getForumIdByShortname(cursor, forum_short)
	if forum_id is None:
		return dontExist('forum')
	thread_forum = getForumByThread(cursor, thread_id)
	if thread_forum is None:
		return dontExist('thread')
	if thread_forum != forum_id:
		return badJson('thread is not in specified forum')
		
	author_id = getUserByEmail(user_email, cursor)
	if author_id is None:
		return dontExist('user')
	
	if parent_id is None:
		path = ''
		isroot=True
	else:	
		path = getParentMatpath(cursor, parent_id)
		isroot = False
	query = ("INSERT INTO post (forum_id, message, author_id"
			", isApproved, isHighlighted, isDeleted, isEdited, isSpam"
			", date, thread_id, isRoot, author_email) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);")
	cursor.execute(query, [forum_id, message, author_id, \
		isApproved, isHighlighted, isDeleted, isEdited, isSpam , date, thread_id, isroot, user_email])
	mysql.connection.commit()
	row = cursor.lastrowid
	
	cursor.execute("UPDATE post SET matpath='"+path+getPathPiece(row)+"' WHERE id="+str(row)+';')
	mysql.connection.commit()
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
	cursor = mysql.connection.cursor()
	if getPostRespById(resp, cursor, id, related) == False:
		return dontExist('post')
	return OK(resp)

