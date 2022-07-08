import requests
from flask import Flask
from flask import request
from flask import Response

import constants
from cache import Cache

app = Flask(__name__)
cache = Cache()

@app.route('/crypto/sign', methods=['GET'])
def sign():
    message = request.args.get('message', default=None, type=str)
    email = request.args.get('email', default=None, type=str)
    if message is None:
        return Response('The input message is required.',
                        status=422,
                        content_type='application/json')

    cached_val = cache.get(message)
    if cached_val is not None:
        return Response(
            cached_val,
            status=200,
            content_type='application/json',
        )

    response = requests.get(constants.SYNTESIA_SIGN_API_URL + '/crypto/sign?message=' + message,
                            headers={'Authorization': constants.AUTH_TOKEN})

    if response.status_code == 502:
        response_message = 'You signature is being evaluated, you will be notified by email when it is ready.'
        if email is None:
            response_message = 'You signature is being evaluated, ' \
                               'to receive notification that it is ready you have to provide your email in request.'
        return Response(
            response_message,
            status=200,
            content_type='application/json',
        )
    cache.put(message, response.text)
    return Response(
        response.text,
        status=response.status_code,
        content_type=response.headers['content-type'],
    )


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
