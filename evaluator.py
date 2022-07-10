import requests
import time
import smtplib
import ssl
import re
from flask import request
from flask import Response
from queue import PriorityQueue
from threading import Thread
from threading import Lock
from email.message import EmailMessage

import constants
from cache import Cache
from logger import Logger


def is_valid_email(email):
    if not re.match(r"^[A-Za-z0-9\.\+_-]+@[A-Za-z0-9\._-]+\.[a-zA-Z]*$", email):
        return False
    return True


def send_email(receiver_email, message, signed, logger):
    context = ssl.create_default_context()
    with smtplib.SMTP(constants.SMTP_SERVER, constants.SMTP_PORT) as server:
        server.ehlo()
        server.starttls(context=context)
        server.ehlo()
        server.login(constants.SMTP_LOGIN, constants.SMTP_PASSWORD)
        msg = EmailMessage()
        msg['Subject'] = 'Your message is signed.'
        msg['From'] = constants.SMTP_LOGIN
        msg['To'] = receiver_email
        msg.set_content('Your message \'{}\' signature is ready. \nSigned message: \'{}\''.format(message, signed))
        server.send_message(msg)
        logger.info('The message was sent by email, content = {}'.format(msg.as_string()))


class Evaluator:
    def __init__(self):
        self.__logger = Logger()
        self.__number_of_hits = 0
        self.__start_time = 0
        self.__cache = Cache()
        self.__queue = PriorityQueue()
        self.__mutex = Lock()
        self.__stop_queue_process = False
        self.__queue_thread = Thread(target=self.__process_queue)
        self.__queue_thread.start()

    def eval(self) -> Response:
        self.__logger.info('Sign request evaluation is started.')
        with self.__mutex:
            current_time = time.time()
            if current_time - self.__start_time >= constants.SECONDS_FOR_HITS_COUNTER_REFRESH:
                self.__logger.info('The number of hits of endpoint is refreshed. '
                                   'Current time is: {}, last time when refreshed was: {}.'
                                   'Currently chosen SECONDS_FOR_HITS_COUNTER_REFRESH is: {}'
                                   .format(current_time, self.__start_time, constants.SECONDS_FOR_HITS_COUNTER_REFRESH))
                self.__start_time = current_time
                self.__number_of_hits = 0

            message = request.args.get('message', default=None, type=str)
            email = request.args.get('email', default=None, type=str)
            self.__logger.info('Input message: {}, email: {} from query string.'.format(message, email))
            if message is None:
                self.__logger.info('Input message is empty, returning 422 status code.')
                return Response('The input message is required.',
                                status=422,
                                content_type='application/json')

            cached_val = self.__cache.get(message)
            if cached_val is not None:
                self.__logger.info('The input message ({}) signature is cached.'.format(message))
                return Response(
                    cached_val,
                    status=200,
                    content_type='application/json',
                )

            if self.__number_of_hits == constants.NUMBER_OF_HITS_PER_MINUTE:
                self.__logger.info('The number of current hits ({}) exceeds number of allowed requests per minute ({})'
                                   .format(self.__number_of_hits, constants.NUMBER_OF_HITS_PER_MINUTE))
                response_message = 'Your signature is being evaluated, you will be notified by email when it is ready.'
                if email is None or not is_valid_email(email):
                    response_message = 'Your signature is being evaluated, ' \
                                       'to receive notification that it is ready ' \
                                       'you have to provide your email in request.'
                self.__logger.info('Message ({}) was put in queue, queue size = {}.'
                                   .format(message, self.get_queue_size))
                self.__queue.put((current_time, message, email))
                return Response(
                    response_message,
                    status=200,
                    content_type='application/json',
                )
            response = requests.get(constants.SYNTHESIA_SIGN_API_URL + '/crypto/sign?message=' + message,
                                    headers={'Authorization': constants.AUTH_TOKEN})
            self.__number_of_hits += 1
            self.__logger.info('Request to Synthesia sign API was made, number of current hits = {}'
                               .format(self.__number_of_hits))
            self.__logger.info('Message ({}) was processed with status_code = {}.'
                               .format(message, response.status_code))
            if response.status_code == 502 or 400 <= response.status_code < 500:
                response_message = 'Your signature is being evaluated, you will be notified by email when it is ready.'
                if email is None:
                    response_message = 'Your signature is being evaluated, ' \
                                       'to receive notification that it is ready you ' \
                                       'have to provide your email in request.'
                self.__logger.info('Message ({}) was put in queue, queue size = {}.'
                                   .format(message, self.get_queue_size))
                self.__queue.put((current_time, message, email))
                return Response(
                    response_message,
                    status=200,
                    content_type='application/json',
                )
            self.__logger.info('The message ({}) was successfully signed with first attempt.'.format(message))
            self.__cache.put(message, response.text)
            return Response(
                response.text,
                status=response.status_code,
                content_type=response.headers['content-type'],
            )

    def stop_queue(self) -> None:
        self.__logger.info('Queue is stopped.')
        with self.__mutex:
            self.__stop_queue_process = True

    def restart_queue(self) -> None:
        self.__logger.info('Queue is restarted.')
        with self.__mutex:
            self.__stop_queue_process = False
        self.__queue_thread.join()
        self.__queue_thread = Thread(target=self.__process_queue)
        self.__queue_thread.start()

    def get_queue_size(self) -> int:
        return self.__queue.qsize()

    def __process_queue(self) -> None:
        while not self.__stop_queue_process:
            self.__logger.info('Queue size is: '.format(self.get_queue_size()))
            while not self.__queue.empty():
                current_time = time.time()
                if current_time - self.__start_time >= constants.SECONDS_FOR_HITS_COUNTER_REFRESH:
                    self.__logger.info('The number of hits of endpoint is refreshed. '
                                       'Current time is: {}, last time when refreshed was: {}.'
                                       'Currently chosen SECONDS_FOR_HITS_COUNTER_REFRESH is: {}.'
                                       .format(current_time, self.__start_time,
                                               constants.SECONDS_FOR_HITS_COUNTER_REFRESH))
                    self.__start_time = current_time
                    self.__number_of_hits = 0

                if self.__number_of_hits == constants.NUMBER_OF_HITS_PER_MINUTE:
                    self.__logger.info('The number of current hits ({}) exceeds number of'
                                       ' allowed requests per minute ({}), next try will be done in queue.'
                                       .format(self.__number_of_hits, constants.NUMBER_OF_HITS_PER_MINUTE))
                    time.sleep(constants.SECONDS_BETWEEN_ATTEMPTS)
                    break

                curr_request = self.__queue.get()
                # Check if message was cached already
                message = curr_request[1]
                email = curr_request[2]
                self.__logger.info('Current item in queue, message = {}, email = {}'.format(message, email))
                cached_val = self.__cache.get(message)
                if cached_val is not None:
                    self.__logger.info('Current item (message = {}, email = {}) is cached already'
                                       .format(message, email))
                    send_email(email, message, cached_val)
                    break

                response = requests.get(constants.SYNTHESIA_SIGN_API_URL + '/crypto/sign?message=' + message,
                                        headers={'Authorization': constants.AUTH_TOKEN})
                self.__number_of_hits += 1
                self.__logger.info('Request to Synthesia sign API was made from queue, number of current hits = {}'
                                   .format(self.__number_of_hits))
                self.__logger.info('Message ({}) was processed with status_code = {}.'
                                   .format(message, response.status_code))
                if response.status_code == 502 or 400 <= response.status_code < 500:
                    self.__logger.info('Message ({}) was put in queue, queue size = {}.'
                                       .format(message, self.get_queue_size))
                    self.__queue.put((current_time + constants.SECONDS_TILL_NEXT_REQUEST_ATTEMPT, message, email))
                    break
                send_email(email, message, response.text)
                self.__logger.info('The message ({}) was successfully signed after a bunch of attempts in queue.'
                                   .format(message))
                self.__cache.put(message, response.text)
                time.sleep(constants.SECONDS_BETWEEN_ATTEMPTS)
            # time.sleep(constants.SECONDS_BETWEEN_ATTEMPTS)
