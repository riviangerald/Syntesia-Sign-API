import requests
import time
from flask import request
from flask import Response
from queue import PriorityQueue
from threading import Thread
from threading import Lock

import constants
from cache import Cache


class Evaluator:
    def __init__(self):
        self.__number_of_hits = 0
        self.__start_time = 0
        self.__cache = Cache()
        self.__queue = PriorityQueue()
        self.__mutex = Lock()
        self.__stop_queue_process = False
        self.__queue_thread = Thread(target=self.__process_queue)
        self.__queue_thread.start()

    def eval(self) -> Response:
        with self.__mutex:
            current_time = time.time()
            if current_time - self.__start_time >= constants.SECONDS_FOR_HITS_COUNTER_REFRESH:
                self.__start_time = current_time
                self.__number_of_hits = 0

            message = request.args.get('message', default=None, type=str)
            email = request.args.get('email', default=None, type=str)
            if message is None:
                return Response('The input message is required.',
                                status=422,
                                content_type='application/json')

            cached_val = self.__cache.get(message)
            if cached_val is not None:
                return Response(
                    cached_val,
                    status=200,
                    content_type='application/json',
                )

            if self.__number_of_hits == constants.NUMBER_OF_HITS_PER_MINUTE:
                self.__queue.put((current_time, message, email))
                response_message = 'You signature is being evaluated, you will be notified by email when it is ready.'
                if email is None:
                    response_message = 'You signature is being evaluated, ' \
                                       'to receive notification that it is ready ' \
                                       'you have to provide your email in request.'
                self.__queue.put((current_time, message, email))
                return Response(
                    response_message,
                    status=200,
                    content_type='application/json',
                )

            response = requests.get(constants.SYNTHESIA_SIGN_API_URL + '/crypto/sign?message=' + message,
                                    headers={'Authorization': constants.AUTH_TOKEN})
            self.__number_of_hits += 1
            if response.status_code == 502 or 400 <= response.status_code < 500:
                response_message = 'You signature is being evaluated, you will be notified by email when it is ready.'
                if email is None:
                    response_message = 'You signature is being evaluated, ' \
                                       'to receive notification that it is ready you ' \
                                       'have to provide your email in request.'
                self.__queue.put((current_time, message, email))
                return Response(
                    response_message,
                    status=200,
                    content_type='application/json',
                )

            self.__cache.put(message, response.text)
            return Response(
                response.text,
                status=response.status_code,
                content_type=response.headers['content-type'],
            )

    def __process_queue(self) -> None:
        while not self.__stop_queue_process:
            while not self.__queue.empty():
                current_time = time.time()
                if current_time - self.__start_time >= constants.SECONDS_FOR_HITS_COUNTER_REFRESH:
                    self.__start_time = current_time
                    self.__number_of_hits = 0
                curr_request = self.__queue.get()
                # Check if message was cached already
                message = curr_request[1]
                cached_val = self.__cache.get(message)
                # TODO: notify customer by email
                if cached_val:
                    break

                if self.__number_of_hits == constants.NUMBER_OF_HITS_PER_MINUTE:
                    time.sleep(constants.SECONDS_BETWEEN_ATTEMPTS)
                    break

                response = requests.get(constants.SYNTHESIA_SIGN_API_URL + '/crypto/sign?message=' + message,
                                        headers={'Authorization': constants.AUTH_TOKEN})
                self.__number_of_hits += 1
                if response.status_code == 502 or 400 <= response.status_code < 500:
                    email = curr_request[2]
                    self.__queue.put((current_time + constants.SECONDS_TILL_NEXT_REQUEST_ATTEMPT, message, email))
                    break

                # TODO: notify customer by email
                self.__cache.put(message, response.text)
                time.sleep(constants.SECONDS_BETWEEN_ATTEMPTS)
            time.sleep(constants.SECONDS_BETWEEN_ATTEMPTS)
