from flask import Flask

from evaluator import Evaluator


def create_app():
    app = Flask(__name__)
    evaluator = Evaluator()

    @app.route('/crypto/sign', methods=['GET'])
    def sign():
        return evaluator.eval()

    return app, evaluator


if __name__ == '__main__':
    app, evaluator = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
