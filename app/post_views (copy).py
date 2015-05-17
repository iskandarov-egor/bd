from app import mysql, app, conn
from flask import request, jsonify
import MySQLdb
from shortcuts import *

@app.route('/db/api/post/create/', methods = ['POST'])
def thread_vote():
	tosend = {}	

		try:
			date = request.json['date']
			thread_id = request.json['thread']
			message = request.json['message']
			user_email = request.json['user']
			forum_short = request.json['forum']
		except:	
			tosend['code'] = 2
			tosend['response'] = "couldn't find some required fields"
			return jsonify(**tosend)
		parent_id = None
		isApproved = False
		isHighlighted = False
		isEdited = False
		isDeleted = False
		isSpam = False
		try:	
			parent_id = request.json['parent']
		try:
			isApproved = request.json['isApproved']
		try:
			isHighlighted = request.json['isHighlighted']
		try:
			isEdited = request.json['isEdited']
		try:
			isDeleted = request.json['isDeleted']
		try:
			isSpam = request.json['isSpam']
						
		#conn =mysql.connect()
		cursor = conn.cursor()
				
		forum_id = getForumIdByShortname(cursor, forum_short)
		if forum_id is None:
			tosend['code'] = 2
			tosend['response'] = "forum doesn't exist"
			return jsonify(**tosend)
		
		author_id = getUserByEmail(user_email, cursor)
		if author_id is None:
			tosend['code'] = 2
			tosend['response'] = "user doesn't exist"
			return jsonify(**tosend)
		
		query = ("INSERT INTO post (forum_id, message, author_id"
				", isApproved, isHighlighted, isDeleted, isEdited, isSpam"
				", date) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s);")
		cursor.execute(query, (forum_id, message, author_id, \
			isApproved, isHighlighted, isDeleted, isEdited, isSpam , date))
		conn.commit()
		
		tosend['code'] = 0
		resp = {}
		resp['date'] = date
		resp['forum'] = forum_short
		resp['id'] = cursor.lastrowid
		resp['isApproved'] = isApproved
		resp['isEdited'] = isEdited
		resp['isHighlighted'] = isHighlighted
		resp['isSpam'] = isSpam
		resp['message'] = message
		resp['parent'] = 'NULL'
		resp['thread'] = thread
		resp['user'] = user_email
		
		tosend['response'] = resp
		cursor.close()

	#except:
	#	tosend['code'] = 4
	#	tosend['response'] = 'unknown error'
	return jsonify(**tosend)

@app.route('/db/apwewei/thread/list/', methods = ['GET'])	
def list_threads():	
	tosend = {}	
	try:
		user_email = request.args.get('user')	
		if user_email is None:
			forum_short = request.args.get('forum')
			user_email = ''
			if forum_short is None:
				tosend['code'] = 2
				tosend['response'] = "forum short name or user email is required"
				return jsonify(**tosend)
		else:
			forum_short = ''		
		
		since = request.args.get('since')
		limit = request.args.get('limit')
		order = request.args.get('order')	
		
		resp = []
		#conn =mysql.connect()
		cursor = conn.cursor()
		
		if getThreadsResp(resp, cursor, forum_short, user_email) == False:
			tosend['code'] = 2
			tosend['response'] = "forum or user do not exist"
			return jsonify(**tosend)
		tosend['code'] = 0
		tosend['response'] = resp
	except:
		tosend['code'] = 4
		tosend['response'] = 'unknown error'
	cursor.close()	
	return jsonify(**tosend)

