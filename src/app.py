from flask import Flask, render_template, Response, jsonify, request

app = Flask(__name__)

@app.route("/")
def root():
    return render_template('./public/index.html');

@app.route('/detect', methods=['POST'])
def detect():
	print(request.get_json())
    return "Received"


if __name__ == '__main__':
    app.run(host='0.0.0.0', threaded=True)