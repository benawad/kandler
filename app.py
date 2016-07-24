from flask import Flask, request
import json
import requests

app = Flask(__name__)

@app.route("/")
def hello():
    return 'Hello!'

@app.route("/webhook", methods=['POST', 'GET'])
def verify():
    if request.method == 'POST':
        data = request.get_json()
        message = data['entry'][0]['messaging'][0]
        params = {'access_token': 'EAAPQfxYLKaMBANW7bFFb5amwHRiuhRGqoK8jPH0GPpHDyTWHNiguz8I3VQq6rjSfEbETuonZBENcndPiYwZCBF66QwBHRcvZBjgdsVVizGhMyOSY42J7KAlp5wX7e0a8KWbKUbZANnjpmVkRUQweVgtN6IsHcsQETdAmW2RfQwZDZD'}
        headers = {'Content-Type': 'application/json'}
        a = {}
        a['recipient'] = {'id':message['sender']['id']}
        a['message'] = {'text':message['message']['text']}
        r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=json.dumps(a))
        print('sc: %s' % r.status_code)
        print(r.text)
        return "ok!", 200
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
