from app import app, mysql, conn
from flask import request, jsonify
import MySQLdb
from shortcuts import *

@app.route('/db/api/thread/listPosts/', methods = ['GET'])
def thread_list_posts():
	thread_id = request.args.get('thread')
	if thread_id is None:
		return didntFind('thread')
	
	resp = []

	sort = request.args.get('sort')
	since = request.args.get('since')
	limit = request.args.get('limit')
	order = request.args.get('order')

	if limit is not None:
		limit=int(limit)
	if sort is None or sort == 'flat':
		extra = sinceOrderLimit(since, order, limit)
		if extra == False:
			return badExtra()
		#conn = mysql.connect()
		cursor = conn.cursor()	
		if False == getPostsResp(resp, cursor, thread_id=thread_id, extra=extra):
			cursor.close()
			#conn.close()
			return dontExist('thread')
	else:
		#conn = mysql.connect()
		cursor = conn.cursor()
		if False == treeSort(cursor, resp, thread_id, sort, since, order, limit):
			cursor.close()
			#conn.close()
			return badExtra()

	cursor.close()
	#conn.close()
	return OK(resp)


@app.route('/db/api/thread/vote/', methods = ['POST'])
def thread_vote():
	if not('vote' in request.json and 'thread' in request.json):
		didntFind('thread id and vote')
	thread_id = request.json['thread']
	vote = request.json['vote']
	if vote != 1 and vote != -1:
		badJson('vote must be 1 or -1')
	
	if vote == 1:
		query = "UPDATE thread SET likes = likes + 1 WHERE id = %s;"
	else:
		query = "UPDATE thread SET dislikes = dislikes + 1 WHERE id = %s;"	
	#conn = mysql.connect()
	cursor = conn.cursor()
	cursor.execute(query, (thread_id))
	conn.commit()

	resp = {}
	getThreadRespById(resp, cursor, thread_id)
	cursor.close()
	#conn.close()
	return OK(resp)


@app.route('/db/api/thread/update/', methods = ['POST'])
def thread_update2():
	try:
		thread_id = request.json['thread']
		slug = request.json['slug']
		message = request.json['message']
		if not areOfType((slug, message), basestring):
			return badTypes()
	except:
		didntFind('thread message, slug and id')
	query = "UPDATE thread SET slug = %s, message = %s WHERE id = %s;"			
	#conn = mysql.connect()
	cursor = conn.cursor()
	cursor.execute(query, (slug, message, thread_id))
	conn.commit()
	
	resp = {}
	if False == getThreadRespById(resp, cursor, thread_id):
		cursor.close()
		#conn.close()
		return dontExist('thread')
	cursor.close()
	#conn.close()
	return OK(resp)

@app.route('/db/api/thread/unsubscribe/', methods = ['POST'])
@app.route('/db/api/thread/subscribe/', methods = ['POST'])
def subscribe():
	try:
		thread_id = request.json['thread']
		email = request.json['user']
	except:
		didntFind('thread id and user email')
	#conn = mysql.connect()
	cursor = conn.cursor()
	if getThreadIdById(cursor, thread_id) is None:
		cursor.close()
		#conn.close()
		return dontExist('thread')
	user_id = getUserByEmail(email, cursor)
	if user_id is None:
		cursor.close()
		#conn.close()
		return dontExist('user')
		
	try:
		if request.url_rule.rule == '/db/api/thread/subscribe/':	
			query = ("INSERT INTO subscription (user_id, thread_id)"
					"VALUES(%s, %s);")
		else:
			query = "DELETE FROM subscription WHERE user_id = %s AND thread_id = %s;"		
		
		cursor.execute(query, (user_id, thread_id))
		conn.commit()
	except:
		pass
	cursor.close()
	#conn.close()
	resp={}
	resp['user'] = email
	resp['thread'] = thread_id			
	return OK(resp)

@app.route('/db/api/thread/close/', methods = ['POST'])	
@app.route('/db/api/thread/open/', methods = ['POST'])
@app.route('/db/api/thread/remove/', methods = ['POST'])
@app.route('/db/api/thread/restore/', methods = ['POST'])
def clopen_thread():
	if not('thread' in request.json):
		return didntFind('thread')
	id = request.json['thread']
	#conn = mysql.connect()
	cursor = conn.cursor()
	if getThreadIdById(cursor, id) is None:
		cursor.close()
		#conn.close()
		return dontExist('thread')
	
	if request.url_rule.rule == '/db/api/thread/close/':	
		toset = "isClosed = TRUE"
	elif request.url_rule.rule == '/db/api/thread/open/':
		toset = "isClosed = FALSE"
	elif request.url_rule.rule == '/db/api/thread/remove/':
		toset = "isDeleted = TRUE"
		query = "UPDATE post SET isDeleted = TRUE WHERE thread_id = %s;"
		cursor.execute(query, id)
		conn.commit()
	else:
		toset = "isDeleted = FALSE"
		query = "UPDATE post SET isDeleted = FALSE WHERE thread_id = %s;"
		cursor.execute(query, id)
		conn.commit()
	query = "UPDATE thread SET "+toset+" WHERE id = %s;"
	cursor.execute(query, id)
	conn.commit()
	cursor.close()
	#conn.close()
	resp = {}
	resp['thread'] = id
	
	return OK(resp)

@app.route('/db/api/forum/listThreads/', methods = ['GET'])
@app.route('/db/api/thread/list/', methods = ['GET'])
def list_threads():
	fromforum = (request.url_rule.rule == '/db/api/forum/listThreads/')
	
	forum_short = request.args.get('forum')
	user_email = request.args.get('user')
	if forum_short is None:
		if fromforum:
			return didntFind('forum shortname')
		if user_email is None:
			return didntFind('forum shortname or user email')
	else:
		if user_email is not None:
			return badJson('both user and forum arguments found')
		
	if fromforum:
		related = request.args.getlist('related')
	else:
		related = []	
	
	since = request.args.get('since')
	limit = request.args.get('limit')
	order = request.args.get('order')	
	
	extra = sinceOrderLimit(since, order, limit)
	if extra == False:
		return badExtra()
	resp = []
	#conn = mysql.connect()
	cursor = conn.cursor()
	if getThreadsResp(resp, cursor, extra, forum_short, user_email, related) == False:
		cursor.close()
		#conn.close()
		return didntFind('forum or user')
	cursor.close()
	#conn.close()
	return OK(resp)


@app.route('/db/api/thread/create/', methods = ['POST'])	
def create_thread():
	try:
		forum_short = request.json['forum']
		title = request.json['title']
		isClosed = request.json['isClosed']
		founder_email = request.json['user']
		date = request.json['date']
		message = request.json['message']
		slug = request.json['slug']
		if not (areOfType((title, date, message, slug), basestring) and type(isClosed)==bool):
			return badTypes()
	except:
		return didntFind()
	if 'isDeleted' in request.json:
		isDeleted = request.json['isDeleted']
		if type(isDeleted) != bool:
			return badTypes()
	else:
		isDeleted = False	
	
	#conn = mysql.connect()
	cursor = conn.cursor()
	founder_id = getUserByEmail(founder_email, cursor)
	if founder_id is None:
		cursor.close()
		#conn.close()
		return dontExist('user')
	forum_id = getForumIdByShortname(cursor, forum_short)
	if forum_id is None:
		cursor.close()
		#conn.close()
		return dontExist('forum')
	
	query = ("INSERT INTO thread (title, slug, creator_id, "
			"message, forum_id, date, isClosed, isDeleted) "
			"VALUES(%s, %s, %s, %s, %s, %s, %s, %s);")
	
	cursor.execute(query, (title, slug, founder_id, message \
	, forum_id, date, isClosed, isDeleted))
	conn.commit()
	cursor.close()
	#conn.close()
	resp = {}
	resp['id'] = cursor.lastrowid
	resp['date'] = date
	resp['forum'] = forum_short
	resp['isClosed'] = isClosed
	resp['isDeleted'] = isDeleted
	resp['message'] = message
	resp['slug'] = slug
	resp['title'] = title
	resp['user'] = founder_email
	
	return OK(resp)


@app.route('/db/api/thread/details/', methods = ['GET'])
def get_thread_details():
	thread_id = request.args.get('thread')
	if thread_id is None:
		return didntFind('thread id')
		
	related = request.args.getlist('related')
	if checkRelated(related, ['user', 'forum']) == False:
		return badJson('related parameter is incorrect')
	
	resp = {}
	#conn = mysql.connect()
	cursor = conn.cursor()
	if getThreadRespById(resp, cursor, thread_id, related) == False:
		cursor.close()
		#conn.close()
		return dontExist('thread')
	cursor.close()
	#conn.close()
	return OK(resp)

