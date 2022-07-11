# Syntesia Sign API

### Description

Service wrapps https://hiring.api.synthesia.io/crypto/sign endpoint and makes <br>
it more reliable to user in terms of avoiding upstream service degradation scenario.

### Usage

`docker-compose build` <br>
`docker-compose up`
<br>
<br>
Make a request, for example: <br>
<br>
`curl "http://localhost:5000/crypto/sign?message=auoooof&email=foo@dummy.com"` <br>
<br>
Request without message provided will return status code `422`. <br>
All other requests should return status code `200` with either base64 signature or message.
<br>
<br>
In case of service degradation scenario for the call you will get either:
<ol>
  <li>no notification when the signature for message will be calculated, if email is not provided in request.</li>
  <li>a notification when the signature for message will be calculated, if email is provided in request.</li>
</ol>

### Testing

You can run tests with: <br>
<br>
`pytest` <br>
<br>
Having dependencies preinstalled firstly from `requirements.txt` <br>
<br>
`pip3 -r requirements.txt` <br>
<br>
Keep in mind, to ru tests locally without docker you need python3 to be installed on your computer. <br>
At the moment tests coverage is rather low due to lack of time. <br>
There is also script for perfomance testing written `./perf_testing/perf_test_base.py` which is helpful in terms <br>
of testing caching, queuing and service restart (aka queue restore).

### System Design


![synthesia_system_design](https://user-images.githubusercontent.com/108991812/178255313-0f30d17a-05c3-439b-8a96-b8f5ef9d4b08.svg)

<br>
<br>
<ol>
  <li>Client request is checked up in cache (lru cache strategy) which is backed up by Redis.</li>
  <li>Main Service Application validates request and redirects it to Synthesia API if rate limit is not exceeded (10 requests per minute as described in tech challenge).</li>
  <li>If there is a valid response from Synthesia API - return in to client.</li>
  <li>If not or if number of requests per minute is greater than limit - place request in queue.</li>
  <li>Operate queue in background, backuping it in Mysql DB.</li>
  <li>If request from queue succeeds in getting response from Synthesia API - notify client by email.</li>
  <li>If application service shutdowns and restarts afterwards - queue will be restored from Mysql DB and continues timed queueing requesting.</li>
</ol>
<br>
<br>

### Bugs, Tradeofs and Issues opened
<ol>
  <li>Graceful shutdown for queue - loss of request might happen.</li>
  <li>Inner Priority Queue vs RabbitMQ (or Kafka?) - topic to discuss. IMHO using any separate service queue in this scenario is an overhead.</li>
  <li>Minor bugs in logging.</li>
  <li>Looks like there is a bug in queue storing timestamp - have seen some artifacts in logs by one of perfomance testing sessions.</li>
  <li>Some proper telemetry should be added in queue to make it reliable.</li>
</ol>

<br>
<br>
Thanks for going so far!

