import time
import string
import random
import requests

emails = ['viachaslau.shreider@gmail.com', 'vyachaslau.shreider@gmail.com', 'dasha_96_10@mail.ru']
messages = [''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(20, 40)) for i in range(60)]
messages *= 2
random.shuffle(messages)

global signed_with_first_attempt
global unsigned_with_first_attempt


def send_requests():
    global signed_with_first_attempt
    global unsigned_with_first_attempt
    signed_with_first_attempt = 0
    unsigned_with_first_attempt = 0
    for i, message in enumerate(messages):
        email = emails[i % len(emails)]
        r = requests.get(url='http://localhost:5000/crypto/sign', params={'message': message, 'email': email})
        text = r.text
        if not (text == 'Your signature is being evaluated, you will be notified by email when it is ready.' or
                text == 'The input message is required.' or
                text == 'Your signature is being evaluated, to receive notification that it is ready you ' 
                        'have to provide your email in request.'):
            signed_with_first_attempt += 1
        else:
            unsigned_with_first_attempt += 1
        time.sleep(1)


if __name__ == '__main__':
    global signed_with_first_attempt
    global unsigned_with_first_attempt
    send_requests()
    print('Number of signed messages within first attempt = {}'.format(signed_with_first_attempt))
    print('Number of unsigned messages within first attempt = {}'.format(unsigned_with_first_attempt))