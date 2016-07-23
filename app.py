from flask import Flask, request

app = Flask(__name__)

@app.route("/")
def hello():
    return 'Hello!'

@app.route("/webhook")
def verify():
    token = request.args.get('hub.verify_token', '')
    mode = request.args.get('hub.mode', '')
    challenge = request.args.get('hub.challenge', '')
    correct_token = 'japanese_sausage_plant'

    if token == correct_token and mode == 'subscribe':
        return challenge
    else:
        return "Something went wrong :("

if __name__ == "__main__":
    app.run()
