from flask import Flask, request
import json
import requests
import os
import plotly
from imgurpython import ImgurClient
import plotly.plotly as py
from plotly.tools import FigureFactory as FF
from datetime import datetime
import ystockquote
import plotly.graph_objs as go
import re
import pandas.io.data as web

app = Flask(__name__)

@app.route("/")
def hello():
    return 'Hello!'

def valid_input(symbol):
    # if re.match("follow\s(.*?)(.*?)\-(.*?)\s(.*?)$", symbol):
        # for x in re.finditer(r"\w+",symbol):
            # print(x)
            # if re.match("^[0-9]$",x.group()):
                # nmin=x.group()
            # elif re.match("^[A-Z]{1,4}$",x.group()):
                # ticker=x.group()
        # print("You will now get updates on "+ticker+" every "+nmin +" minutes")
    # elif re.match("follow\s(.*?)(.*?)\-(.*?)\s(.*?)$", symbol):
        # for x in re.finditer(r"\w+",symbol):
            # print(x)
            # if re.match("^[A-Z]{1,4}$",x.group()):
                # ticker=x.group()
        # print("You will now get updates on "+ticker+" every 1 minute")
    return re.match("^[A-Z]{1,5}$", symbol)

def news(recipient_id, symbol):
    pass

def twitter(recipient_id, symbol):
    pass

@app.route("/webhook", methods=['POST', 'GET'])
def verify():
    if request.method == 'POST':
        data = request.get_json()
        # loop through unread messages
        for m in data['entry'][0]['messaging']:
            if 'postback' in m:
                payload = m['postback']['payload']
                payload = payload.split("|")
                if payload[0] == "twitter":
                    twitter(m['sender']['id'], payload[1])
                elif payload[0] == "data":
                    sym_data = ystockquote.get_all(payload[1])
                    for k, v in sym_data.items():
                        send_message(m['sender']['id'], "%s: %s" % (k, v))
                elif payload[0] == "news":
                    news(m['sender']['id'], payload[1])
                else:
                    send_message(m['sender']['id'], "Please enter a symbol like AAPL")
            if 'message' in m:
                symbol = m['message']['text']
                symbol = symbol.strip().upper()
                if not valid_input(symbol):
                    send_message(m['sender']['id'], "Please enter a symbol like AAPL")
                else:
                    try:
                        send_picture(m['sender']['id'], symbol)
                    except Exception as e:
                        print("ERROR")
                        print(e)
                    price = ystockquote.get_price(symbol)
                    if "N/A" == price:
                        send_message(m['sender']['id'], "Unknown symbol")
                        send_message(m['sender']['id'], "Please enter a symbol like AAPL")
                    else:
                        send_thumbnail(m['sender']['id'], symbol, price)

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


def make_candlechart(symbol):
    plotly.plotly.sign_in(username='benawad', api_key=os.environ['PLOTLY_KEY'])
    df = web.DataReader(symbol, 'yahoo', datetime(2016, 9, 1), datetime(2016, 9, 30))
    fig = FF.create_candlestick(df.Open, df.High, df.Low, df.Close, dates=df.index)
    fig['layout'] = go.Layout(title=symbol)
    py.image.save_as(fig, filename='tgraph.png')


def send_picture(recipient_id, symbol):
    make_candlechart(symbol)
    img_url = upload_image_to_imgur("tgraph.png")
    print(img_url)

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


def send_thumbnail(recipient_id, symbol, price):
    message_data = {
        'recipient': {'id': recipient_id},
        'message': {
            # "attachment":{
              # "type":"template",
              # "payload":{
                # "template_type":"generic",
                # "elements":[
                  # {
                    # "title":symbol,
                    # "subtitle": "Price: %s" % price,
                    # "buttons":[
                      # {
                        # "type":"postback",
                        # "title":"More data",
                        # "payload": "data|%s" % symbol,
                      # },
                      # {
                        # "type":"postback",
                        # "title":"News",
                        # "payload": "news|%s" % symbol,
                      # },
                      # {
                        # "type":"postback",
                        # "title":"Tweets",
                        # "payload": "twitter|%s" % symbol,
                      # },
                    # ]
                  # }
                # ]
              # }
            # }
            "attachment": {
         "type": "template",
           "payload": {
                   "elements": [
              {
                    "title": "The Startup Tapes #007 \u2014 Software Dreams of Community",

                   "item_url": "https://www.producthunt.com/podcasts/the-startup-tapes-007-software-dreams-of-community?utm_campaign=producthunt-api&utm_medium=api&utm_source=Application%3A+Phfb+%28ID%3A+3399%29",

                   "subtitle": "Sarah helps humans scale Google\u2019s fastest-growing software",

                  "image_url": "https://ph-files.imgix.net/c3d343b7-b5ac-45dd-b8d9-d4944e3dba36?auto=format&fit=crop&h=570&w=430"

                },

                 {

                    "title": "Mavic Pro",

                     "item_url": "https://www.producthunt.com/tech/mavic-pro?utm_campaign=producthunt-api&utm_medium=api&utm_source=Application%3A+Phfb+%28ID%3A+3399%29",

                    "subtitle": "A foldable 4K drone by DJI that fits in your hand",

                     "image_url": "https://ph-files.imgix.net/7985907f-6173-4506-91dd-2a3e2690cac7?auto=format&fit=crop&h=570&w=430"

              },

               {

                     "title": "SMACtalk - Importance of Social Video for Business Success",

                    "item_url": "https://www.producthunt.com/podcasts/smactalk-importance-of-social-video-for-business-success?utm_campaign=producthunt-api&utm_medium=api&utm_source=Application%3A+Phfb+%28ID%3A+3399%29",
                    "subtitle": "The future of video",
                   "image_url": "https://ph-files.imgix.net/6d805b7a-0b7d-4736-bf3e-27fe49e6630d?auto=format&fit=crop&h=570&w=430"

                },

                 {

                     "title": "Circulation",
                    "item_url": "https://www.producthunt.com/tech/circulation?utm_campaign=producthunt-api&utm_medium=api&utm_source=Application%3A+Phfb+%28ID%3A+3399%29",

                    "subtitle": "A new vision for non\u2011emergency medical transportation.",

                     "image_url": "https://ph-files.imgix.net/d7f3ed77-1888-4805-a4a4-d0f1775576fb?auto=format&fit=crop&h=570&w=430"

                },
                 {

                   "title": "Awesome Office - The Most Important Thing",

                    "item_url": "https://www.producthunt.com/podcasts/awesome-office-the-most-important-thing?utm_campaign=producthunt-api&utm_medium=api&utm_source=Application%3A+Phfb+%28ID%3A+3399%29",

                     "subtitle": "Sean Kelly on life's most important lessons",
                    "image_url": "https://ph-files.imgix.net/200cd210-008e-4d42-a3df-02db363b5162?auto=format&fit=crop&h=570&w=430"
              }
        }
    }
    headers = {'Content-Type': 'application/json'}
    params = {'access_token': os.environ['PAGE_ACCESS_TOKEN']}
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=json.dumps(message_data))
    if r.status_code == 200:
        print('Sent "%s" to %s' % (recipient_id, message_data))
    else:
        print('FAILED to send "%s" to %s' % (recipient_id, message_data))
        print('REASON: %s' % r.text)

if __name__ == "__main__":
    app.run()
