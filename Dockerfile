FROM python:3.7

RUN adduser -D api
RUN apk add build-base
RUN apk add python3-dev
RUN apk add libffi-dev
RUN apk add openssl-dev

WORKDIR /home/api

COPY requirements.txt requirements.txt
RUN python3 -m venv env
RUN env/bin/pip3 install -r requirements.txt
RUN env/bin/pip3 install gunicorn

COPY api api
COPY runprod.sh ./
RUN chmod +x runprod.sh
RUN chown -R api:api ./
USER api

ENV FLASK_APP api/__init__.py
ENV FLASK_DEBUG 0
ENV AUTH0_CALLBACK_URL http://localhost:8000/callback/
ENV FLASK_SECRET_KEY SADASDVASD
ENV AUTH0_CLIENT_SECRET ABC
ENV AWS_ACCESS_ID ABC
ENV AWS_ACCESS_KEY ABC
EXPOSE 5000
ENTRYPOINT ["./runprod.sh"]
