from flask import Flask

from evaluator import Evaluator

app = Flask(__name__)
evaluator = Evaluator()


@app.route('/crypto/sign', methods=['GET'])
def sign():
    return evaluator.eval()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
