from flask import Flask
from flask import request

app = Flask(__name__)


@app.route('/')
def hello_world():
    return 'Hello World!'


@app.route('/recette')
def getRecette():
    response = request.args
    ingredient = response['ingredient']
    note = response['note']
    tempDePrep = response['tempDePrep']
    difficulty = response['difficulty']
    return recetteName


if __name__ == '__main__':
    app.run()
