FROM python:3.7

WORKDIR /home/api

COPY requirements.txt requirements.txt
RUN pip install -r ./requirements.txt
RUN pip install gunicorn

COPY api api
COPY runprod.sh ./
RUN chmod +x runprod.sh

EXPOSE 5000
ENTRYPOINT ["./runprod.sh"]
