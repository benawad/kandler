from flask import Flask, request
import json
import requests
import os
import plotly
from imgurpython import ImgurClient
import plotly.plotly as py
from plotly.tools import FigureFactory as FF
from datetime import datetime

import pandas.io.data as web

app = Flask(__name__)

@app.route("/")
def hello():
    return 'Hello!'

@app.route("/webhook", methods=['POST', 'GET'])
def verify():
    if request.method == 'POST':
        data = request.get_json()
        print(data)
        # loop through unread messages
        for m in data['entry'][0]['messaging']:
            if 'message' in m:
                # send_message(m['sender']['id'], m['message']['text'])
                send_picture(m['sender']['id'], m['message']['text'])
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

def upload_image_to_imgur(path):
    client_id = os.environ['IMGUR_CLIENT_ID']
    client_secret = os.environ['IMGUR_CLIENT_SECRET']


    client = ImgurClient(client_id, client_secret)
    url = client.upload_from_path(path)
    return url['link']

def send_picture(recipient_id, symbol):
    plotly.plotly.sign_in(username='benawad', api_key=os.environ['PLOTLY_KEY'])
    df = web.DataReader(symbol, 'yahoo', datetime(2009, 3, 1), datetime(2009, 4, 1))
    fig = FF.create_candlestick(df.Open, df.High, df.Low, df.Close, dates=df.index)
    py.image.save_as(fig, filename='tgraph.png')

    # img_url = upload_image_to_imgur("tgraph.png")
    # print(img_url)
    img_url = "https://afternoon-dawn-15659.herokuapp.com/tgraph.png"

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
