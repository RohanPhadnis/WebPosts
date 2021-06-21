import os
import json
import bson
from flask import *
from flask_pymongo import *


app = Flask('WebPosts')
app.config['MONGO_URI'] = 'mongodb+srv://anyone:xyz@flask.ngjrl.mongodb.net/flask_react_db?retryWrites=true&w=majority'
mongo = PyMongo(app)


@app.route('/', methods=['GET'])
def home():
    if request.method == 'GET':
        return render_template('home.html')


@app.route('/delete/<identity>', methods=['GET'])
def delete(identity):
    if request.method == 'GET':
        mongo.db.entries.delete_one({'_id': bson.ObjectId(identity)})
        return redirect('/view')


@app.route('/view', methods=['GET'])
def view():
    if request.method == 'GET':
        docs = list(mongo.db.entries.find({}))
        return render_template('view.html', docs=docs)


@app.route('/json', methods=['GET'])
def api():
    if request.method == 'GET':
        encoder = json.JSONEncoder()
        docs = [{key: str(val) for key, val in doc.items()} for doc in mongo.db.entries.find({})]
        docs = encoder.encode(docs)
        return docs


@app.route('/post', methods=['GET', 'POST'])
def post():
    if request.method == 'GET':
        return render_template('post.html')
    elif request.method == 'POST':
        resp = dict(request.form)
        mongo.db.entries.insert_one(resp)
        return redirect('/post')


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, port=port)
