FROM python:3.11-slim

RUN apt update && apt install -y g++ build-essential

COPY . /app

WORKDIR /app/web
RUN pip install --upgrade pip && pip install -r requirements.txt

WORKDIR /app/cpp
RUN g++ server.cpp -o server

WORKDIR /app
RUN chmod +x entrypoint.sh

EXPOSE 5000

CMD ["./entrypoint.sh"]
