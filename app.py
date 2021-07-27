import time
import os
import json
import bson
from flask import *
from flask_pymongo import *


app = Flask('WebPosts')
app.config['MONGO_URI'] = 'mongodb+srv://anyone:xyz@flask.ngjrl.mongodb.net/flask_react_db?retryWrites=true&w=majority'
mongo = PyMongo(app)
lock_time = 60 * 15
encoder = json.JSONEncoder()


@app.route('/', methods=['GET'])
def home():
    if request.method == 'GET':
        return render_template('home.html')


@app.route('/reg', methods=['GET', 'POST'])
def reg():
    if request.method == 'GET':
        return render_template('reg.html')
    elif request.method == 'POST':
        resp = dict(request.form)
        if len(list(mongo.db.user.find({'user': resp['user']}))) > 0:
            return render_template('reg.html', msg='username already exists')
        else:
            mongo.db.user.insert_one(resp)
            resp['time'] = time.time()
            mongo.db.session.insert_one(resp)
            user_session = list(mongo.db.session.find({'user': resp['user']}))[0]
            return redirect('/view/'+str(user_session['_id']))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    elif request.method == 'POST':
        resp = dict(request.form)
        user = list(mongo.db.user.find({'user': resp['user']}))
        if len(user) == 0:
            return render_template('login.html', msg='login does not exist')
        else:
            user = user[0]
            if user['pass'] != resp['pass']:
                return render_template('login.html', msg='incorrect password')
            else:
                resp['time'] = time.time()
                mongo.db.session.delete_many({'user': resp['user']})
                mongo.db.session.insert_one(resp)
                user_session = list(mongo.db.session.find({'user': resp['user']}))[0]
                return redirect('/view/' + str(user_session['_id']))


@app.route('/view/<user_session>', methods=['GET'])
def view(user_session):
    if request.method == 'GET':
        session = list(mongo.db.session.find({'_id': bson.ObjectId(user_session)}))
        if len(session) == 0:
            return redirect('/login')
        else:
            session = session[0]
            if time.time() - session['time'] >= lock_time:
                mongo.db.session.delete_one({'_id': bson.ObjectId(user_session)})
                return redirect('/login')
            else:
                docs = list(mongo.db.entry.find({'user': session['user']}))
                return render_template('view.html', docs=docs, session=user_session)


@app.route('/post/<user_session>', methods=['GET', 'POST'])
def post(user_session):
    if request.method == 'GET':
        session = list(mongo.db.session.find({'_id': bson.ObjectId(user_session)}))
        if len(session) == 0:
            return redirect('/login')
        else:
            session = session[0]
            if time.time() - session['time'] >= lock_time:
                mongo.db.session.delete_one({'_id': bson.ObjectId(user_session)})
                return redirect('/login')
            else:
                return render_template('post.html', session=user_session)
    elif request.method == 'POST':
        session = list(mongo.db.session.find({'_id': bson.ObjectId(user_session)}))[0]
        resp = dict(request.form)
        resp['user'] = session['user']
        mongo.db.entry.insert_one(resp)
        return redirect('/post/{}'.format(str(session['_id'])))


@app.route('/confirm/<username>', methods=['GET'])
def confirm(username):
    print(username)
    user = list(mongo.db.session.find({'user': username}))
    print(user)
    if len(user) == 0:
        return encoder.encode({'login': False, 'session': ''})
    else:
        user = user[0]
        if time.time() - user['time'] > lock_time:
            return encoder.encode({'login': False, 'session': ''})
        else:
            return encoder.encode({'login': True, 'session': str(user['_id'])})


@app.route('/api/<user_session>', methods=['GET'])
def api(user_session):
    if request.method == 'GET':
        session = list(mongo.db.session.find({'_id': bson.ObjectId(user_session)}))
        if len(session) == 0:
            return encoder.encode(['please login'])
        else:
            session = session[0]
            if time.time() - session['time'] >= lock_time:
                mongo.db.session.delete_one({'_id': bson.ObjectId(user_session)})
                return encoder.encode(['please login'])
            else:
                docs = list(mongo.db.entry.find({'user': session['user']}))
                return encoder.encode(docs)


@app.route('/delete/<user_session>/<entry_id>')
def delete(user_session, entry_id):
    if request.method == 'GET':
        session = list(mongo.db.session.find({'_id': bson.ObjectId(user_session)}))
        if len(session) == 0:
            return redirect('/login')
        else:
            session = session[0]
            if time.time() - session['time'] >= lock_time:
                mongo.db.session.delete_one({'_id': bson.ObjectId(user_session)})
                return redirect('/login')
            else:
                mongo.db.entry.delete_one({'_id': bson.ObjectId(entry_id)})
                return redirect('/view/{}'.format(user_session))


@app.route('/rdelete/<user_session>/<entry_id>')
def rdelete(user_session, entry_id):
    if request.method == 'GET':
        session = list(mongo.db.session.find({'_id': bson.ObjectId(user_session)}))
        if len(session) == 0:
            return encoder.encode(['please login'])
        else:
            session = session[0]
            if time.time() - session['time'] >= lock_time:
                mongo.db.session.delete_one({'_id': bson.ObjectId(user_session)})
                return encoder.encode(['please login'])
            else:
                mongo.db.entry.delete_one({'_id': bson.ObjectId(entry_id)})
                return redirect('/api/{}'.format(user_session))


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, port=port)
