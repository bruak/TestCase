FROM python:3.11-slim

RUN apt update && apt install -y g++ build-essential

COPY . /app

WORKDIR /app/web
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

WORKDIR /app
RUN chmod +x entrypoint.sh

EXPOSE 5000

CMD ["/bin/bash", "./entrypoint.sh"]
