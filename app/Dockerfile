FROM python:3.8.1-slim-buster
COPY requirements.txt /
RUN pip install --upgrade pip && pip install -r /requirements.txt
COPY ./ /app
WORKDIR /app
EXPOSE 8080
CMD ["python","app.py"]
