FROM ubuntu:latest

RUN apt-get update && apt-get install -y \
    python3.9 \
    python3-pip

WORKDIR /app

COPY . /app

RUN apt-get update
RUN python3 -m pip install wheel
RUN pip3 --no-cache-dir install -r requirements.txt

EXPOSE 5000

CMD ["python3", "app.py"]