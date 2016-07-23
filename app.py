from flask import Flask, request

app = Flask(__name__)

@app.route("/")
def hello():
    return 'Hello!'

@app.route("/webhook")
def verify():
    print(request.args)
    return str(request.args)

if __name__ == "__main__":
    app.run()
