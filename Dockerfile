FROM python:3

COPY . /srv/

WORKDIR /srv

RUN pip install -r requirements.txt

EXPOSE 9020

CMD ["python", "server.py"]
