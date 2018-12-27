FROM python:3.7

WORKDIR /home/api

COPY requirements.txt requirements.txt
RUN pip install -r ./requirements.txt
RUN pip install gunicorn

COPY api api
COPY runprod.sh ./
RUN chmod +x runprod.sh

ENV FLASK_APP api/__init__.py
ENV FLASK_DEBUG 0
ENV AUTH0_CALLBACK_URL http://localhost:8000/callback/
ENV FLASK_SECRET_KEY SADASDVASD
ENV AUTH0_CLIENT_SECRET ABC
ENV AWS_ACCESS_ID ABC
ENV AWS_ACCESS_KEY ABC
EXPOSE 5000
ENTRYPOINT ["./runprod.sh"]
