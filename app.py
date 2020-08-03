import os
from flask import g, Flask, request, redirect, jsonify, send_from_directory, render_template, url_for
from flask_cors import CORS, cross_origin
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
import json
import sqlite3
from sqlite3 import Error
import logging

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__, static_url_path='/static')
app.config['UPLOAD_FOLDER'] = 'static/'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://games.db'
db = SQLAlchemy(app)
cors = CORS(app)


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect('games.db')
    def make_dicts(cursor, row):
        return dict((cursor.description[idx][0], value)
                    for idx, value in enumerate(row))
    db.row_factory = make_dicts
    return db

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def smol_query(query):
    conn = sqlite3.connect("games.db")
    cur = conn.cursor()
    cur.execute(query)
    conn.commit()
    conn.close()

@app.route('/api')
def api():
    app.logger.debug(str(request))
    # IF a command has been run...
    if request.args.get('command'):

        # Check/Run LISTGAMES command
        if request.args.get('command') == 'listGames':
            games = []
            for game in query_db('select * from games'):
                app.logger.debug(type(game))
                games += [game]
            return json.dumps(games)
        
        if request.args.get('command') == 'updateGames':
            if request.args.get('data'):
                data = request.args.get('data')
                data = json.loads(data)
                for item in data:
                #query = "update votes set vote = '" + voteval + "' where id = '" + str(existing_vote[0]['id']) + "';"
                    query = "update games set title='" + item['title'] + "', slug='" + item['slug'] + "', description='" + item['description'] + "', url='" + item['url'] + "' where id=" + item['id'] + ";"
                    smol_query(query)
                return "success!"

        if request.args.get('command') == 'addBlank':
            query = "insert into games default values;"
            conn = sqlite3.connect("games.db")
            cur = conn.cursor()
            cur.execute(query)
            conn.commit()
            conn.close()
            return "success!"

        if request.args.get('command') == 'deleteGame':
            if request.args.get('value'):
                delid = request.args.get('value')
                query = "delete from games where id="+delid
                conn = sqlite3.connect("games.db")
                cur = conn.cursor()
                cur.execute(query)
                conn.commit()
                conn.close()
                return "success!"

            

        # Check/Run VOTE command
        if request.args.get('command') == 'vote':
            if request.args.get('title'):
                title = request.args.get('title')
                if request.args.get('value'):
                    votevalx = request.args.get('value')
                    if votevalx == 'up':
                        voteval = "1"
                    if votevalx == 'down':
                        voteval = "-1"
                    if voteval is None:
                        return "Invalid vote value! ;)"
                    else:
                        #votee = str(request.remote_addr)
                        headers_list = request.headers.getlist("X-Forwarded-For")
                        votee = headers_list[0] if headers_list else request.remote_addr

                        query = "select * from votes;" 
                        app.logger.debug(query_db(query))
                        # Check if they voted, if not add, if so update
                        query = "select * from votes where votee = '" + votee + "' and title = '" + title + "';" 
                        existing_vote = query_db(query)
                        app.logger.debug(existing_vote)
                        if existing_vote:
                            app.logger.debug(existing_vote[0]['id'])
                            query = "update votes set vote = '" + voteval + "' where id = '" + str(existing_vote[0]['id']) + "';"
                            conn = sqlite3.connect("games.db")
                            cur = conn.cursor()
                            cur.execute(query)
                            conn.commit()
                            conn.close()
                            #query_db(query)
                            app.logger.debug("ran " + query)
                        else:
                            query = "insert into votes (votee, title, vote) values " + "('" + votee + "', " + "'" + title+ "', " + "'" + voteval + "')" + ";"
                            app.logger.debug(query)
                            conn = sqlite3.connect("games.db")
                            cur = conn.cursor()
                            cur.execute(query)
                            conn.commit()
                            conn.close()
                            app.logger.debug("ran " + query)
                        query = "update games set score=(select sum(vote) from votes where title='"+title+"') where title='"+title+"'"
                        app.logger.debug(query)
                        conn = sqlite3.connect("games.db")
                        cur = conn.cursor()
                        cur.execute(query)
                        conn.commit()
                        conn.close()
                        #return votee + " voted " + voteval + " for " + title
                        return "Voted successfully!"

    return """Invalid Request :) 
    Try something like <a href='?command=listGames'>listGames</a> 
    or <a href='?command=vote&title=Krunker&value=1'> vote up for krunker </a> /
    <a href='?command=vote&title=Krunker&value=-1'> vote down for krunker </a>"""

@app.route('/')
def index():
    return render_template("index.htm")

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/sssssssssssssssupersecretupload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect('/guicifersecret')
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post enctype=multipart/form-data>
      <input type=file name=file>
      <input type=submit value=Upload>
    </form>
    '''

@app.route('/sssssssssssssssupersecret')
def gui():
    return render_template("gucci.htm")   
  
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=False)