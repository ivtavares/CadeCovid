FROM python:3.8-alpine
COPY requirements.txt /
RUN pip install -r /requirements.txt
COPY ./ /app
WORKDIR /app
CMD ["python","app-flask.py"]