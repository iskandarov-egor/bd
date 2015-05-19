from flask import Flask
#from flaskext.mysql import MySQL
from flask.ext.mysqldb import MySQL
app = Flask(__name__)
mysql = MySQL()

app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '250246'
app.config['MYSQL_DB'] = 'forumdb2'
app.config['MYSQL_HOST'] = 'localhost'
#app.config['MYSQL_DATABASE_USER'] = 'root'
#app.config['MYSQL_DATABASE_PASSWORD'] = '2502460'
#app.config['MYSQL_DATABASE_DB'] = 'forumforum'
#app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)
#conn = mysql.connect()
from app import user_views
from app import forum_views, thread_views, post_views




