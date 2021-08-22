import os
import time
import json
import bson
from flask import *
from flask_pymongo import *

app = Flask('WebPosts')
app.config['MONGO_URI'] = 'mongodb+srv://anyone:xyz@flask.ngjrl.mongodb.net/flask_react_db?retryWrites=true&w=majority'
mongo = PyMongo(app)
lock_time = 60 * 15
stat_time = 1628457475.023316
encoder = json.JSONEncoder()


@app.route('/', methods=['GET'])
def home():
    if request.method == 'GET':
        mongo.db.stats.insert_one({'page': 'home', 'ip': str(request.remote_addr), 'user': 'None', 'time': time.time()})
        return render_template('home.html')


@app.route('/reg', methods=['GET', 'POST'])
def reg():
    if request.method == 'GET':
        mongo.db.stats.insert_one({'page': 'reg', 'ip': str(request.remote_addr), 'user': 'None', 'time': time.time()})
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
        mongo.db.stats.insert_one({'page': 'login', 'ip': str(request.remote_addr), 'user': 'None', 'time': time.time()})
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
                mongo.db.stats.insert_one(
                    {'page': 'view', 'ip': str(request.remote_addr), 'user': session['user'], 'time': time.time()})
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
                mongo.db.stats.insert_one(
                    {'page': 'post', 'ip': str(request.remote_addr), 'user': session['user'], 'time': time.time()})
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
            mongo.db.stats.insert_one(
                {'page': 'confirm', 'ip': str(request.remote_addr), 'user': user['user'], 'time': time.time()})
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
                for n in range(len(docs)):
                    docs[n]['_id'] = str(docs[n]['_id'])
                mongo.db.stats.insert_one(
                    {'page': 'api', 'ip': str(request.remote_addr), 'user': session['user'], 'time': time.time()})
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
                mongo.db.stats.insert_one(
                    {'page': 'delete', 'ip': str(request.remote_addr), 'user': session['user'], 'time': time.time()})
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
                mongo.db.stats.insert_one(
                    {'page': 'rdelete', 'ip': str(request.remote_addr), 'user': session['user'], 'time': time.time()})
                return redirect('/api/{}'.format(user_session))


@app.route('/info/<user_session>', methods=['GET'])
def info(user_session):
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
                session['_id'] = str(session['_id'])
                mongo.db.stats.insert_one(
                    {'page': 'info', 'ip': str(request.remote_addr), 'user': session['user'], 'time': time.time()})
                return encoder.encode(session)


@app.route('/stats', methods=['GET'])
def stats():
    if request.method == 'GET':
        mongo.db.stats.insert_one(
            {'page': 'stats', 'ip': str(request.remote_addr), 'user': 'None', 'time': time.time()})
        docs = list(mongo.db.stats.find({}))
        for n in range(len(docs)):
            docs[n]['time'] = docs[n]['time'] - stat_time
            docs[n]['_id'] = str(docs[n]['_id'])
        max_time = max([docs[n]['time'] for n in range(len(docs))])
        step_time = max_time / 50
        events = {n: [] for n in range(51)}
        for doc in docs:
            events[int(doc['time'] / step_time)].append(doc)
        rects = [[n/51, 1, 0.01, 0] for n in range(51)]
        for n in range(len(events)):
            rects[n][3] = len(events[n])
        max_height = max([rect[3] for rect in rects])
        for n in range(len(rects)):
            rects[n][3] = rects[n][3] / max_height
            rects[n][1] = 1 - rects[n][3]
        e = [events[n] for n in range(51)]
        return render_template('stats.html', events=e, rects=rects)


@app.route('/apistats', methods=['GET'])
def apistats():
    if request.method == 'GET':
        docs = list(mongo.db.stats.find({}))
        for d in docs:
            d['_id'] = str(d['_id'])
        return encoder.encode(docs)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, port=port)
