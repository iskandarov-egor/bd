from numconv import *
from flask import jsonify
import ujson

def getStatus(resp, cursor, table):
	query = "SELECT COUNT(*) FROM " + table + ";"
	cursor.execute(query)
	resp[table] = cursor.fetchone()[0]

def badTypes():
	return badJson('argument types are incorrect')

def badExtra():
	return badJson('since, order or limit are incorrect')

def arePresent(keys, json):
	return all (k in json for k in keys)

def areOfType(things, typ):
	if not (isinstance(things[0], typ) or things[0] is None):
		return False
	result = True
	for thing in things:
		if not (isinstance(thing, typ) or thing is None):
			result = False
	return result

def wrongTypes():
	return badJson('incorrect argument types')

def treeSort(cursor, resp, thread_id, sort, since, order, limit):
	root_query = "SELECT matpath AS mpath FROM post WHERE isRoot=TRUE AND thread_id=%s"
	if order == 'desc' or order is None:
		extra = ' ORDER BY root.mpath DESC'
	elif order == 'asc':
		extra = ' ORDER BY root.mpath ASC'
	else:
		return False
	extra += ', child.matpath ASC'
	if since is not None:
		root_extra = " AND date>'"+str(since)+"'"
	else:
		root_extra = ''
	if limit is not None:
		root_extra += ' LIMIT ' + str(limit)
		if sort == 'tree':		
			extra += ' LIMIT ' + str(limit)
	root_query += root_extra
	query = ("SELECT "+postParams+" FROM"
			" (" + root_query + ") AS root"
			" INNER JOIN post child"
			" ON child.matpath LIKE CONCAT(root.mpath, %s)"
			+ extra + ';')


	cursor.execute(query, [thread_id, '%'])
	alldata = cursor.fetchall()
	for data in alldata:
		subresp = {}
		parsePostData(subresp, cursor, data)
		resp.append(subresp)

def getThreadRespById(resp, cursor, id, related = [], known = {}):
	query = "SELECT sql_no_cache " + thread_fields +" FROM thread WHERE id = %s;"
	cursor.execute(query, [id])
	data = cursor.fetchone()
	if data is None:
		return False
	
	parseThreadData(resp, cursor, data, related=related, known=known)
	return True

def getThreadsResp(resp, cursor,  extra, forum_id=None, creator_email=None,  related = [], known = {}):	
	query = "SELECT  sql_no_cache " + thread_fields +" FROM thread WHERE "
	if forum_id is not None:
		#forum_id = getForumIdByShortname(cursor, forum_short)
		#if forum_id is None:
		#	return False
		query += "forum_id = "+str(forum_id)+extra+";"
	else:
		creator_id = getUserByEmail(creator_email, cursor)
		if creator_id is None:
			return False
		query += "creator_id = " + str(creator_id)+extra+";"
	cursor.execute(query)
	data = cursor.fetchall()
	lim = len(data)
	for i in range(0, lim):
		subresp = {}
		parseThreadData(subresp, cursor, data[i], related=related, known=known)
		resp.append(subresp)
	return True	

def countPostsInThread(cursor, id):
	cursor.execute("SELECT  sql_no_cache posts FROM thread WHERE id = " + str(id) + ";")
	return cursor.fetchone()[0]

def parseThreadData(resp, cursor, data, related = [], known = {}):
	if 'user' in related:
		uresp = {}
		getUserResp(uresp, cursor, id = data[2])
		resp['user'] = uresp
	else:
		resp['user'] = getUserEmailById(cursor, data[2])
	
	if 'forum' not in known:
		if 'forum' in related:
			fresp = {}
			getForumResp(fresp, cursor, id=data[6])
			resp['forum'] = fresp
		else:
			resp['forum'] = getForumShortnameById(cursor, data[6])	
	else:
		resp['forum'] = known['forum']
	
	resp['date'] = str(data[7])
	resp['dislikes'] = data[5]
	resp['isClosed'] = data[8]
	resp['isDeleted'] = data[9]
	resp['likes'] = data[4]
	resp['message'] = data[3]
	resp['points'] = data[4] - data[5]
	resp['slug'] = data[1]
	resp['title'] = data[0]
	resp['posts'] = data[11]
	resp['id'] = data[10]

thread_fields = "title, slug, creator_id, message, likes, dislikes, forum_id, date, isClosed, isDeleted, id, posts"





def checkRelated(related, allowedValues):
	for rel in related:
		if rel not in allowedValues:
			return False
	return True

def getParents(cursor, extra = ''):
	cursor.execute("SELECT id FROM post WHERE matpath IS NULL " + extra + ' ;')
	parents = []
	parseArrOfArrs(cursor.fetchall(), parents)
	return parents

def getChildPosts(cursor, path, extra, resp):
	return ''
	query = "SELECT date, id, matpath FROM post WHERE matpath LIKE '" + path + "'" + extra + ";"
	cursor.execute(query)
	toappend = []
	alldata = cursor.fetchall()
	for data in alldata:
		subresp = {}
		subresp['date'] = str(data[0])
		subresp['id'] = data[1]
		subresp['matpath'] = data[2]
		resp.append(subresp)
		getChildPosts(cursor, path, extra, resp)

def mystr(tostr):
	if type(tostr) == str or type(tostr) == unicode:
		return "'" + tostr + "'"
	else:
		return str(tostr)

def sinceOrderLimit(since, order, limit, orderby='date', sinceWhat='date'):
	if since is not None:
		extra = ' AND '+sinceWhat+' >= ' + mystr(since) + ' '
	else:
		extra = ' '
	if order is not None:
		orderextra = getOrderExtra(order, orderby)
		if orderextra == False:
			return False
		extra += orderextra
	
	if limit is not None:
		try:
			limit = int(limit)
		except:
			return False
		extra += ' LIMIT ' + str(limit)
	return extra	

def getOrderExtra(order, by):
	if order is not None and not isinstance(order, basestring):
		return False
	if order is None or order.lower() == 'desc':
		return "ORDER BY " + by + " DESC"
	elif order == 'asc':
		return "ORDER BY " + by + " ASC"
	else:
		return False

def jsonOrFalse(json, key):
	try:
		return json[key]
	except:
		return False
		
def dontExist(what):
	tosend = {}
	tosend['code'] = 1	
	tosend['response'] = what + " doesn't exist"
	return ujson.dumps(tosend)

def badJson(err):
	tosend = {}
	tosend['code'] = 3	
	tosend['response'] = err
	return ujson.dumps(tosend)

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
	return ujson.dumps(tosend)

def getPathPiece(id):


	base36 = int2str(id, radix=36)



	return str(len(base36)) + base36

def getParentMatpath(cursor, id):
	query = 'SELECT  sql_no_cache matpath FROM post WHERE id = %s'
	cursor.execute(query, [id])
	return cursor.fetchone()[0]



def getParentByMatpath(path):
	if path is None:
		return None
	num=int(path[0])
	path2 = path[num+1 :]
	while path2 != '':
		prev=path[1:num+1]
		path = path2
		num=int(path[0])
		path2 = path[num+1 :]
	return str2int(prev, 36)



def parseArrOfArrs(arr, whereto):
	for f in arr:
		for ff in f:
			whereto.append(ff)



def getForumByThread(cursor, id):
	query = ("SELECT  sql_no_cache forum_id FROM thread WHERE id = %s;")
	cursor.execute(query, [id])
	forum = cursor.fetchone()
	if forum is None:
		return None
	return forum[0]

def getForumIdByShortname(cursor, shortname):
	query = ("SELECT id FROM forum WHERE short_name = %s;")
	cursor.execute(query, [shortname])
	forum = cursor.fetchone()
	if forum is None:
		return None
	else:
		return forum[0]	

def getForumIdByName(cursor, name):
	query = ("SELECT id FROM forum WHERE name = %s;")
	cursor.execute(query, [name])
	forum = cursor.fetchone()
	if forum is None:
		return None
	else:
		return forum[0]


def getForumResp(resp, cursor, id=None, short_name=None, name=None, related = []):
	if short_name is not None:
		id = getForumIdByShortname(cursor, short_name)
	elif name is not None:
		id = getForumIdByName(cursor, name)
	if id is None:
		return None	
	query = ("SELECT short_name, name, founder_id FROM forum WHERE id = %s;")
	cursor.execute(query, [id])
	data = cursor.fetchone()

	resp['short_name'] = data[0]
	resp['name'] = data[1]
	resp['id'] = id
	if 'user' in related:
		user = {}
		getUserResp(user, cursor, id=data[2])
		resp['user'] = user
	else:
		resp['user'] = getUserEmailById(cursor, data[2])



def getForumShortnameById(cursor, id):
	query = ("SELECT short_name FROM forum WHERE id = %s;")
	cursor.execute(query, [id])
	return cursor.fetchone()[0]
	
def getUserByEmail(email, cursor):
	query = ("SELECT id  sql_no_cache FROM user WHERE email = %s;")
	cursor.execute(query, [email])
	user = cursor.fetchone()
	if user is not None:
		return user[0]
	else:
		return None	


user_fields = 'about, email, user.id, isAnonymous, user.name, username, hasFollowers, hasFollowees, hasSubscriptions'

def parseUserData(cursor, resp, data):
	resp['email'] = data[1]
	resp['about'] = data[0]
	resp['id'] = data[2]
	resp['isAnonymous'] = data[3]
	resp['name'] = data[4]
	
	resp['username'] = data[5]
	if data[6] == 0:
		resp['followers'] = []
	else:
		getFollowers(cursor, data[2], resp)
	if data[7] == 0:
		resp['followees'] = []
	else:
		getFollowees(cursor, data[2], resp)
	if data[8] == 0:
		resp['subscriptions'] = []
	else:
		resp['subscriptions'] = getSubscriptions(cursor, data[2])
	
#returns user id
def getUserResp(resp, cursor, email = None, id = None):
	if(id is None):
		query = "SELECT  sql_no_cache " + user_fields + " FROM user WHERE email = %s;"
		cursor.execute(query, [email])
	else:
		query = "SELECT  sql_no_cache " + user_fields + " FROM user WHERE id = %s;"
		cursor.execute(query, [id])
	data = cursor.fetchone()
	if data is None:
		return False

	parseUserData(cursor, resp, data)
	return data[2]

def getUserEmailById(cursor, id):
	query = ("SELECT  sql_no_cache email FROM user WHERE id = %s;")
	cursor.execute(query, [id])
	email = cursor.fetchone()[0]
	
	return email


getFollowers_query = ("SELECT email FROM user u "
			"INNER JOIN following f "
			"ON f.follower_id = u.id "
			"WHERE f.followee_id = %s ;")
def getFollowers(cursor, id, resp):	
	cursor.execute(getFollowers_query, [id])
	followers = cursor.fetchall()
	resp['followers'] = []
	parseArrOfArrs(followers, resp['followers'])

getFollowees_query = ("SELECT email FROM user u "
			"INNER JOIN following f "
			"ON f.followee_id = u.id "
			"WHERE f.follower_id = %s ;")
def getFollowees(cursor, id, resp):
	cursor.execute(getFollowees_query, [id])		
	following = cursor.fetchall()
	
	resp['following'] = []
	parseArrOfArrs(following, resp['following'])

def getFollowersResp(cursor, id, resp, wees=False, extra = ''):	
	if wees:
		query = ("SELECT " + user_fields + " FROM user "
			"INNER JOIN following f "
			"ON f.followee_id = user.id "
			"WHERE f.follower_id = %s ") + extra + ';'
	else:
		query = ("SELECT " + user_fields + " FROM user"
		" INNER JOIN following f"
		" ON f.follower_id = user.id"
		" WHERE f.followee_id = %s " + extra + ';')
			
	cursor.execute(query, [id])		
	alldata = cursor.fetchall()
	
	for data in alldata:
		subresp = {}
		parseUserData(cursor, subresp, data)
		resp.append(subresp)

def getUsersResp(resp, cursor,  extra, forum_short):
	forum_id = getForumIdByShortname(cursor, forum_short)
	if forum_id is None:
		return False
	query = ("SELECT DISTINCT "+user_fields+" FROM post p"
	" INNER JOIN user ON user.id = p.author_id WHERE p.forum_id = " 
			+str(forum_id)+' ' +extra+";")
	cursor.execute(query)
	alldata = cursor.fetchall()
	
	for data in alldata:
		subresp = {}
		parseUserData(cursor, subresp, data)
		resp.append(subresp)
	return True

#id must exist
def getSubscriptions(cursor, id):
	cursor.execute('SELECT thread_id FROM subscription WHERE user_id = ' + str(id) + ';')
	subs = []
	parseArrOfArrs(cursor.fetchall(), subs)
	return subs
	

def parsePostData(resp, cursor, data, related = [], known = {}):
	if 'user' in known:
		resp['user'] = known['user']
	else:
		if 'user' in related:
			uresp = {}
			getUserResp(uresp, cursor, id = data[5])
			resp['user'] = uresp
		else:
			resp['user'] = getUserEmailById(cursor, data[5])
	if 'thread' in related:
		tresp = {}
		getThreadRespById(tresp, cursor, data[12], related=[], known=known)
		resp['thread'] = tresp
	else:
		resp['thread'] = data[12]
	if 'forum' not in known:
		if 'forum' in related:
			fresp = {}
			getForumResp(fresp, cursor, id=data[1])
			resp['forum'] = fresp
		else:
			resp['forum'] = getForumShortnameById(cursor, data[1])
	else:
		resp['forum'] = known['forum']
	resp['id'] = data[0]	
	resp['date'] = str(data[11])
	resp['dislikes'] = data[4]
	resp['isApproved'] = data[6]
	resp['isDeleted'] = data[8]
	resp['isEdited'] = data[9]
	resp['isHighlighted'] = data[7]
	resp['isSpam'] = data[10]
	resp['likes'] = data[3]
	resp['message'] = data[2]
	resp['points'] = data[3] - data[4]
	if data[14] == 1:
		resp['parent'] = None
	else:
		resp['parent'] = getParentByMatpath(data[13])

postParams = ("id, forum_id, message, likes, dislikes, author_id"
	", isApproved, isHighlighted, isDeleted, isEdited, isSpam, date, thread_id, matpath, isRoot")
postParams2 = "matpath, id"
def parsePostData2(resp, cursor, data):
	resp['path'] = data[0]

def getThreadIdById(cursor, id):
	cursor.execute('SELECT  sql_no_cache id FROM thread WHERE id=%s;', [id])
	id = cursor.fetchone()

	if id is None:
		return None
	else:
		return id[0]

def getPostRespById(resp, cursor, id, related = []):
	query = "SELECT sql_no_cache " + postParams + " FROM post WHERE id = %s;"

	cursor.execute(query, [id])
	
	data = cursor.fetchone()
	if data is None:
		return False
	
	parsePostData(resp, cursor, data, related)
	return True
	
def getPostsResp(resp, cursor, forum_id=None, thread_id=None, user_email=None, extra='', related=[], known = {}):
	query = ("SELECT sql_no_cache " + postParams + " FROM post WHERE ")
	if forum_id is not None:
		param = forum_id #getForumIdByShortname(cursor, forum_short)
		if param is None:
			return False
		query += "forum_id=%s "
	elif thread_id is not None:
		param = int(thread_id)
		if getThreadIdById(cursor, thread_id) is None:
			return False
		query += "thread_id=%s "
	else: #user
		param = getUserByEmail(user_email, cursor)
		if param is None:
			return False
		query += "author_id=%s "
	query += extra + ';'
	cursor.execute(query, [param])
	alldata = cursor.fetchall()
	for data in alldata:
		subresp = {}
		parsePostData(subresp, cursor, data, related=related, known=known)
		resp.append(subresp)
		
