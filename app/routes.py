from app import app
from flask import jsonify, abort, make_response, request
from flask_httpauth import HTTPBasicAuth
import postgresql
import json

auth = HTTPBasicAuth()
tasks = [
    {
        'id': 1,
        'title': u'By grocires',
        'description': u'Milk, Cheese, Pizza, Fruit, Tylenol',
        'done': False
    },
    {
        'id': 2,
        'title': u'Learn Python',
        'description': u'Need to find a good Python tutorial',
        'done': False
    }
]
def db_conn():
    return postgresql.open('pq://postgres@localhost')

def to_json(data):
    return json.dumps(data) + "\n"

def resp(code, data):
    return flask.Response(
        status=code,
        mimetype="application/json",
        response=to_json(data)
    )

def todo_validate():
    errors = []
    json = flask.request.get_json()
    if json is None:
        errors.append(
            "No JSON sent. "
        )
        return (None, errors)

    for field_name in ['title']:
        if type(json.get(field_name)) is not str:
            errors.append(
                "Field '{}' is missing or not a string".format(field_name)
            )
    return (json, errors)

def affected_num_to_code(cnt):
    code = 200
    if cnt == 0:
        code = 404
    return code

@auth.get_password
def get_password(username):
    if username == 'ilya':
        return 'python'
    return None

@auth.error_handler
def unauthorized():
    return make_response(jsonify({'error': 'Unauthorized acces'}), 403)

@app.route('/api', methods=['GET'])
# @auth.login_required
def get_tasks():
    with db_conn() as db:
        tuples = db.query("SELECT id, title, description, done FROM todo")
        todo = []
        for (id, title, description, done) in tuples:
            todo.append({"id": id, "title": title, "description": description, "done": done})
    return jsonify({'tasks': todo})

@app.route('/api/<int:task_id>', methods=['GET'])
def det_task(task_id):
    task = list(filter(lambda t: t['id'] == task_id, tasks))
    
    if len(task) == 0:
        abort(404)
    return jsonify({'task': task[0]})

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)

@app.route('/api', methods=['POST'])
def create_task():
    
    if not request.json or not 'title' in request.json:
        abort(400)
    with db_conn() as db:
        insert = db.prepare(
            "INSERT INTO todo (title, description, done) VALUES ($1, $2, $3) " + "RETURNING id")
        [(todo_id,)] = insert(json['title'], json['description'], json['done'])
        
   
    return jsonify({'task': todo_id}), 201

@app.route('/api/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    task = list(filter(lambda t: t['id'] == task_id, tasks))
    if len(task) == 0:
        abort(404)
    if not request.json:
        abort(400)
    if 'title' in request.json and type(request.json['title']) != str:
        abort(400)
    if 'description' in request.json and type(request.json['description']) is not str:
        abort(400)
    if 'done' in request.json and type(request.json['done']) is not bool:
        abort(400)
    task[0]['title'] = request.json.get('title', task[0]['title'])
    task[0]['description'] = request.json.get('description', task[0]['description'])
    task[0]['done'] = request.json.get('done', task[0]['done'])
    return jsonify({'task': task[0]})

@app.route('/api/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    task = list(filter(lambda t: t['id'] == task_id, tasks))
    if len(task) == 0:
        abort(404)
    tasks.remove(task[0])
    return jsonify({'result': True})

