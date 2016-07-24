from flask import Flask, request
import json
import requests
import os

app = Flask(__name__)

@app.route("/")
def hello():
    return 'Hello!'

@app.route("/webhook", methods=['POST', 'GET'])
def verify():
    if request.method == 'POST':
        headers = {'Content-Type': 'application/json'}
        params = {'access_token': os.environ['PAGE_ACCESS_TOKEN']}
        data = request.get_json()
        for m in data['entry'][0]['messaging']:
            if 'message' in m:
                a = {}
                a['recipient'] = {'id':m['sender']['id']}
                a['message'] = {'text':m['message']['text']}
                r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=json.dumps(a))
                print('sc: %s' % r.status_code)
                print(r.text)
        return "ok!", 200
    else:
        token = request.args.get('hub.verify_token', '')
        mode = request.args.get('hub.mode', '')
        challenge = request.args.get('hub.challenge', '')
        correct_token = os.environ['VERIFY_TOKEN']

        if token == correct_token and mode == 'subscribe':
            return challenge, 200
        else:
            return "Something went wrong :(", 403

if __name__ == "__main__":
    app.run()
