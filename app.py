import requests
from flask import Flask
from flask import request
from flask import Response

import constants


app = Flask(__name__)


@app.route('/crypto/sign', methods=['GET'])
def sign():
    message = request.args.get('message', default=None, type=str)
    email = request.args.get('email', default=None, type=str)
    if message is None:
        return Response('The input message required', status=422, mimetype='application/json')

    r = requests.get(constants.SYNTESIA_SIGN_API_URL + '/crypto/sign?message=' + message,
                     headers={'Authorization': constants.AUTH_TOKEN})
    return Response(
        r.text,
        status=r.status_code,
        content_type=r.headers['content-type'],
    )


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)