from flask import Flask, request
import json

app = Flask(__name__)

@app.route("/")
def hello():
    return 'Hello!'

@app.route("/webhook", methods=['POST', 'GET'])
def verify():
    if request.method == 'POST':
        print('form: %s' % request.form)
        print('data: %s' % request.data)
        data = json.loads(str(request.data))
        # message1 = data['entry'][0]['messaging'][0]
        # message['recipient'] = {'id':request.data['entry']}
        return data['entry'][0]['messaging'][0], 200
    else:
        token = request.args.get('hub.verify_token', '')
        mode = request.args.get('hub.mode', '')
        challenge = request.args.get('hub.challenge', '')
        correct_token = 'japanese_sausage_plant'

        if token == correct_token and mode == 'subscribe':
            return challenge, 200
        else:
            return "Something went wrong :(", 403

if __name__ == "__main__":
    app.run()
