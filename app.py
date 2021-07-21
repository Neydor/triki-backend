import os

import boto3
from flask import Flask, jsonify, make_response, request

app = Flask(__name__)

victoryPosition = [[0,1,2],[3,4,5],[6,7,8],[0,3,6],[1,4,7],[2,5,8],[0,4,8],[2,4,6]]

dynamodb_client = boto3.client('dynamodb')

if os.environ.get('IS_OFFLINE'):
    dynamodb_client = boto3.client(
        'dynamodb', region_name='localhost', endpoint_url='http://localhost:8000'
    )


USERS_TABLE = os.environ['USERS_TABLE']


@app.route('/users/<string:user_id>')
def get_user(user_id):
    result = dynamodb_client.get_item(
        TableName=USERS_TABLE, Key={'userId': {'S': user_id}}
    )
    item = result.get('Item')
    if not item:
        return jsonify({'error': 'Could not find user with provided "userId"'}), 404

    return jsonify(
        {'userId': item.get('userId').get('S'), 'name': item.get('name').get('S'),'victorias': item.get('victorias').get('N')}
    )


@app.route('/users', methods=['POST'])
def create_user():
    user_id = request.json.get('userId')
    name = request.json.get('name')
    victorias = request.json.get('victorias')
    if not user_id or not name:
        return jsonify({'error': 'Please provide both "userId" and "name"'}), 
    dynamodb_client.put_item(
        TableName=USERS_TABLE, Item={'userId': {'S': user_id}, 'name': {'S': name},'victorias': {'N': victorias}}
    )

    return jsonify({'userId': user_id, 'name': name,'victorias':victorias})

@app.route('/turnoo', methods=['POST'])
def checkWinner():
    newCells = request.json.get('newCells')
    nombrePlayer1 = request.json.get('nombrePlayer1')
    nombrePlayer2 = request.json.get('nombrePlayer2')

    for x in range(len(victoryPosition)):
        v1 =victoryPosition[x][0]
        v2 = victoryPosition[x][1]
        v3 = victoryPosition[x][2]
        if newCells[v1] and newCells[v1] == newCells[v2] and newCells[v1] == newCells[v3]:
            # ganador fijo
            try:
                ganador = nombrePlayer1 if newCells[v1] == 'X'else nombrePlayer2
                result = dynamodb_client.get_item(TableName=USERS_TABLE, Key={'userId': {'S': ganador}})
                item = result.get('Item')
                if not item:
                    try:
                        dynamodb_client.put_item(TableName=USERS_TABLE, Item={'userId': {'S': ganador}, 'name': {'S': ganador},'victorias': {'N': "1"}})
                    except Exception as exp:
                        return jsonify({"statusCode": 200,"headers": {'Access-Control-Allow-Origin': '*','Access-Control-Allow-Credentials': True,},"body": {'error':"no guardo por primera vez","ganador":ganador,"item":item}})
                else:
                    try:
                        victoryAc= int(item.get('victorias').get('N')) + 1

                        dynamodb_client.put_item(TableName=USERS_TABLE, Item={'userId': {'S': ganador}, 'name': {'S': item.get('name').get('S')},'victorias': {'N': str(victoryAc)}})
                    except:
                        return jsonify({"statusCode": 200,"headers": {'Access-Control-Allow-Origin': '*','Access-Control-Allow-Credentials': True,},"body": {'error':"no actualizo","ganador":ganador,"item":item}})
                return jsonify({"statusCode": 200,"headers": {'Access-Control-Allow-Origin': '*','Access-Control-Allow-Credentials': True,},"body": {'winner':newCells[v1],"victoryMove":victoryPosition[x],'next':False}})
            except Exception as inst:
                return jsonify({"statusCode": 200,"headers": {'Access-Control-Allow-Origin': '*','Access-Control-Allow-Credentials': True,},"body": {'error':inst}})
                
    flagNull = 0
    for x in newCells:
        if x is None:
            # empate //hacer funcion optimizada luego
            flagNull = 1
    if flagNull == 0:      
        return jsonify({"statusCode": 200,"headers": {'Access-Control-Allow-Origin': '*','Access-Control-Allow-Credentials': True,},"body": {"winner":None,'victoryMove':[0,1,2,3,4,5,6,7,8],'next':False}})
    return jsonify({"statusCode": 200,"headers": {'Access-Control-Allow-Origin': '*','Access-Control-Allow-Credentials': True,},"body": {'next':True}})

@app.errorhandler(404)
def resource_not_found(e):
    return make_response(jsonify(error='Not found!'), 404)
