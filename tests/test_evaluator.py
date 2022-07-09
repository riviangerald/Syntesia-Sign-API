from unittest.mock import patch

import pytest
import requests
import requests_mock
from flask import Flask

import constants
from evaluator import Evaluator


def create_app(requests_mock):
    headers = {'Authorization': constants.AUTH_TOKEN, 'content-type': 'application/json'}
    requests_mock.get('https://hiring.api.synthesia.io/crypto/sign?message=hi',
                      headers=headers,
                      status_code=200,
                      text='dB98Ijdzndk6wf/lnLu92z23YCVCvwsfUdB8KlQC2b0ExjLzDcJ4UleqaArz+cardH1lI4'
                           '8gU/NkGc648EXhWkqsDka1nL7FdBjVmZp8vWmNsN0y3BeUt61j6PdURfsnbAj6utIZO5aNX'
                           'DS88jtYJScgqtsfbfW4aNeb1eGcHOI=')
    app = Flask(__name__)
    evaluator = Evaluator()

    @app.route('/crypto/sign', methods=['GET'])
    def sign():
        return evaluator.eval()

    return app, evaluator


@pytest.fixture
def mock_test_timeout(monkeypatch):
    monkeypatch.setattr('constants.SECONDS_BETWEEN_ATTEMPTS', 0)


def test_ctor(mock_test_timeout):
    evaluator = Evaluator()
    evaluator.stop_queue()
    assert evaluator._Evaluator__number_of_hits == 0


def test_eval_no_params(mock_test_timeout, requests_mock):
    a, e = create_app(requests_mock)
    e.stop_queue()
    with a.test_client() as client:
        response = client.get('/crypto/sign', query_string={})
        assert response.status_code == 422
        assert response.content_type == 'application/json'
        assert response.data.decode('UTF-8') == 'The input message is required.'


def test_eval(mock_test_timeout, requests_mock):
    a, e = create_app(requests_mock)
    e.stop_queue()
    with a.test_client() as client:
        response = client.get('/crypto/sign', query_string={'message': 'hi'})
        assert response.status_code == 200
        assert response.data.decode('UTF-8') == 'dB98Ijdzndk6wf/lnLu92z23YCVCvwsfUdB8KlQC2b0ExjLzDcJ4Ul' \
                                                'eqaArz+cardH1lI48gU/NkGc648EXhWkqsDka1nL7FdBjVmZp8vWmNs' \
                                                'N0y3BeUt61j6PdURfsnbAj6utIZO5aNXDS88jtYJScgqtsfbfW4aNeb1eGcHOI='
