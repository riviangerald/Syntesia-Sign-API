import time

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
    requests_mock.get('https://hiring.api.synthesia.io/crypto/sign?message=buy',
                      headers=headers,
                      status_code=200,
                      text='WF0nvA3qPOmjCWRndEXFshCiwG99L/BM9zeTcls8bSpB7e4Hq6AY'
                           'DvNFtjfnH+MdN5y3rFbGa9Y5ekDDcCWLsaZ4pQy40Cy7snkrLJiyv'
                           '1Wmo74bvs/cgpfKdY6+1AApLTnzd4gFiEZDcIOEEg7HZO+SO3+fSTz+bl5hkzAdvkM=')
    requests_mock.get('https://hiring.api.synthesia.io/crypto/sign?message=bye',
                      headers=headers,
                      status_code=200,
                      text='j9+6IWsmJpAuFRPNIz+xVu5WqxQJ4a8GjYRxGWjR/FF5T9ZEoapYPfy'
                           'nRYkuHWGFnmoxHbjkVEEAbKmRvpiovXgOdWLBkoMRDFHIWfCr9wm7mL'
                           'kXujuXdf/mUbodL3FMg/6vjOT56D4jiQgn8FpMCkJ4SjwwGPAR92G4WZj0rPA=')
    app = Flask(__name__)
    evaluator = Evaluator()

    @app.route('/crypto/sign', methods=['GET'])
    def sign():
        return evaluator.eval()

    return app, evaluator


@pytest.fixture
def mock_test_timeout(monkeypatch):
    monkeypatch.setattr('constants.SECONDS_BETWEEN_ATTEMPTS', 0)
    monkeypatch.setattr('evaluator.send_email', lambda x, y, z, logger: 0)
    monkeypatch.setattr('evaluator.Evaluator.put_to_queue', Evaluator.put)
    monkeypatch.setattr('evaluator.Evaluator.get_from_queue', Evaluator.get)


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


def test_eval_cached(mock_test_timeout, requests_mock):
    a, e = create_app(requests_mock)
    e.stop_queue()
    with a.test_client() as client:
        response = client.get('/crypto/sign', query_string={'message': 'hi'})
        assert e._Evaluator__cache.get('hi') == 'dB98Ijdzndk6wf/lnLu92z23YCVCvwsfUdB8KlQC2b0ExjLzDcJ4Ul' \
                                                'eqaArz+cardH1lI48gU/NkGc648EXhWkqsDka1nL7FdBjVmZp8vWmNs' \
                                                'N0y3BeUt61j6PdURfsnbAj6utIZO5aNXDS88jtYJScgqtsfbfW4aNeb1eGcHOI='


def test_eval_message_queued(mock_test_timeout, requests_mock, monkeypatch):
    monkeypatch.setattr('constants.NUMBER_OF_HITS_PER_MINUTE', 1)
    a, e = create_app(requests_mock)
    e.stop_queue()
    with a.test_client() as client:
        _ = client.get('/crypto/sign', query_string={'message': 'hi'})
        response = client.get('/crypto/sign', query_string={'message': 'buy'})
        assert response.status_code == 200
        assert response.data.decode('UTF-8') == 'Your signature is being evaluated, to receive ' \
                                                'notification that it is ready you have to provide ' \
                                                'your email in request.'


def test_eval_message_queued_with_notification(mock_test_timeout, requests_mock, monkeypatch):
    monkeypatch.setattr('constants.NUMBER_OF_HITS_PER_MINUTE', 1)
    a, e = create_app(requests_mock)
    e.stop_queue()
    with a.test_client() as client:
        _ = client.get('/crypto/sign', query_string={'message': 'hi', 'email': 'foo@bar.com'})
        response = client.get('/crypto/sign', query_string={'message': 'buy', 'email': 'foo@bar.com'})
        assert response.status_code == 200
        assert response.data.decode('UTF-8') == 'Your signature is being evaluated, ' \
                                                'you will be notified by email when it is ready.'


def test_eval_message_queued_with_notification_invalid_email(mock_test_timeout, requests_mock, monkeypatch):
    monkeypatch.setattr('constants.NUMBER_OF_HITS_PER_MINUTE', 1)
    a, e = create_app(requests_mock)
    e.stop_queue()
    with a.test_client() as client:
        _ = client.get('/crypto/sign', query_string={'message': 'hi', 'email': 'foo@bar.com'})
        response = client.get('/crypto/sign', query_string={'message': 'buy', 'email': 'foo123.com'})
        assert response.status_code == 200
        assert response.data.decode('UTF-8') == 'Your signature is being evaluated, ' \
                                                'to receive notification that it is ready ' \
                                                'you have to provide your email in request.'


def test_eval_simulate_refresh_rate(mock_test_timeout, requests_mock, monkeypatch):
    monkeypatch.setattr('constants.NUMBER_OF_HITS_PER_MINUTE', 1)
    monkeypatch.setattr('constants.SECONDS_FOR_HITS_COUNTER_REFRESH', 1)
    a, e = create_app(requests_mock)
    e.stop_queue()
    with a.test_client() as client:
        response_1 = client.get('/crypto/sign', query_string={'message': 'hi', 'email': 'foo@bar.com'})
        response_2 = client.get('/crypto/sign', query_string={'message': 'buy', 'email': 'foo@bar.com'})
        response_3 = client.get('/crypto/sign', query_string={'message': 'bye', 'email': 'foo@bar.com'})
        assert response_1.data.decode('UTF-8') == 'dB98Ijdzndk6wf/lnLu92z23YCVCvwsfUdB8KlQC2b0ExjLzDcJ4Ul' \
                                                  'eqaArz+cardH1lI48gU/NkGc648EXhWkqsDka1nL7FdBjVmZp8vWmN' \
                                                  'sN0y3BeUt61j6PdURfsnbAj6utIZO5aNXDS88jtYJScgqtsfbfW4aNeb1eGcHOI='
        assert response_2.data.decode('UTF-8') == 'Your signature is being evaluated, ' \
                                                  'you will be notified by email when it is ready.'
        assert response_3.data.decode('UTF-8') == 'Your signature is being evaluated, ' \
                                                  'you will be notified by email when it is ready.'
        time.sleep(1)
        response_3 = client.get('/crypto/sign', query_string={'message': 'bye', 'email': 'foo@bar.com'})
        assert response_3.data.decode('UTF-8') == 'j9+6IWsmJpAuFRPNIz+xVu5WqxQJ4a8GjYRxGWjR/FF5T9ZEoapYP' \
                                                  'fynRYkuHWGFnmoxHbjkVEEAbKmRvpiovXgOdWLBkoMRDFHIWfCr9w' \
                                                  'm7mLkXujuXdf/mUbodL3FMg/6vjOT56D4jiQgn8FpMCkJ4SjwwGPAR92G4WZj0rPA='


def test_eval_simulate_queueing(mock_test_timeout, requests_mock, monkeypatch):
    monkeypatch.setattr('constants.NUMBER_OF_HITS_PER_MINUTE', 1)
    a, e = create_app(requests_mock)
    e.stop_queue()
    with a.test_client() as client:
        client.get('/crypto/sign', query_string={'message': 'hi', 'email': 'foo@bar.com'})
        client.get('/crypto/sign', query_string={'message': 'buy', 'email': 'foo@bar.com'})
        client.get('/crypto/sign', query_string={'message': 'bye', 'email': 'foo@bar.com'})
        assert e.get_queue_size() == 2
        monkeypatch.setattr('constants.NUMBER_OF_HITS_PER_MINUTE', 10)
        monkeypatch.setattr('constants.SECONDS_FOR_HITS_COUNTER_REFRESH', 0)
        e.restart_queue()
        time.sleep(1)
        e.stop_queue()
        assert e.get_queue_size() == 0


def test_eval_simulate_several_attempts_queueing(mock_test_timeout, requests_mock, monkeypatch):
    monkeypatch.setattr('constants.NUMBER_OF_HITS_PER_MINUTE', 1)
    a, e = create_app(requests_mock)
    with a.test_client() as client:
        headers = {'Authorization': constants.AUTH_TOKEN, 'content-type': 'application/json'}
        requests_mock.get('https://hiring.api.synthesia.io/crypto/sign?message=hi1',
                          headers=headers,
                          status_code=502)
        monkeypatch.setattr('constants.NUMBER_OF_HITS_PER_MINUTE', 4)
        monkeypatch.setattr('constants.SECONDS_BETWEEN_ATTEMPTS', 0)
        client.get('/crypto/sign', query_string={'message': 'hi1', 'email': 'foo@bar.com'})
        time.sleep(1)
        assert e.get_queue_size() == 1
        assert e._Evaluator__number_of_hits == 4
        monkeypatch.setattr('constants.SECONDS_BETWEEN_ATTEMPTS', 1)
        monkeypatch.setattr('constants.NUMBER_OF_HITS_PER_MINUTE', 5)
        requests_mock.get('https://hiring.api.synthesia.io/crypto/sign?message=hi1',
                          headers=headers,
                          status_code=200)
        assert e.get_queue_size() == 1
        assert e._Evaluator__cache.get('hi1') is None
        time.sleep(2)
        assert e.get_queue_size() == 0
        assert e._Evaluator__cache.get('hi1') is not None
        e.stop_queue()


def test_eval_simulate_clear_of_cached_queueing(mock_test_timeout, requests_mock, monkeypatch):
    monkeypatch.setattr('constants.NUMBER_OF_HITS_PER_MINUTE', 1)
    a, e = create_app(requests_mock)
    e.stop_queue()
    with a.test_client() as client:
        headers = {'Authorization': constants.AUTH_TOKEN, 'content-type': 'application/json'}
        requests_mock.get('https://hiring.api.synthesia.io/crypto/sign?message=hi1',
                          headers=headers,
                          status_code=502)
        monkeypatch.setattr('constants.NUMBER_OF_HITS_PER_MINUTE', 10)
        monkeypatch.setattr('constants.SECONDS_BETWEEN_ATTEMPTS', 0)
        client.get('/crypto/sign', query_string={'message': 'hi1', 'email': 'foo@bar.com'})
        client.get('/crypto/sign', query_string={'message': 'hi1', 'email': 'foo@bar.com'})
        client.get('/crypto/sign', query_string={'message': 'hi1', 'email': 'foo@bar.com'})
        client.get('/crypto/sign', query_string={'message': 'hi1', 'email': 'foo@bar.com'})
        assert e.get_queue_size() == 4
        assert e._Evaluator__number_of_hits == 4
        assert e._Evaluator__cache.is_empty()
        requests_mock.get('https://hiring.api.synthesia.io/crypto/sign?message=hi1',
                          headers=headers,
                          status_code=200)
        e.restart_queue()
        time.sleep(1)
        assert e._Evaluator__number_of_hits == 5
        assert e.get_queue_size() == 0
        assert not e._Evaluator__cache.is_empty()
        e.stop_queue()
