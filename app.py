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
        data = request.get_json()
        # loop through unread messages
        for m in data['entry'][0]['messaging']:
            if 'message' in m:
                # send_message(m['sender']['id'], m['message']['text'])
                img_url = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcT4gAlQuMrYW2quJAXYEWydvHBzLMcFDY6HrcX_emZdJQfcA4UfEt4G374"
                send_picture(m['sender']['id'], img_url)
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

def send_message(recipient_id, message):
    message_data = {
        'recipient': {'id' : recipient_id},
        'message': {'text' : message}
    }
    headers = {'Content-Type': 'application/json'}
    params = {'access_token': os.environ['PAGE_ACCESS_TOKEN']}
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=json.dumps(message_data))
    if r.status_code == 200:
        print('Sent "%s" to %s' % (recipient_id, message))
    else:
        print('FAILED to send "%s" to %s' % (recipient_id, message))
        print('REASON: %s' % r.text)

def send_picture(recipient_id, img_url):
    message_data = {
        'recipient': {'id': recipient_id},
        'message': {
            'attachment': {
                "type": "image",
                "payload": {
                        "url": img_url,
                    }
                }
            }
        }
    headers = {'Content-Type': 'application/json'}
    params = {'access_token': os.environ['PAGE_ACCESS_TOKEN']}
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=json.dumps(message_data))
    if r.status_code == 200:
        print('Sent "%s" to %s' % (recipient_id, img_url))
    else:
        print('FAILED to send "%s" to %s' % (recipient_id, img_url))
        print('REASON: %s' % r.text)

if __name__ == "__main__":
    app.run()
