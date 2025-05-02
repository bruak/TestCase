#!/bin/bash

echo "Working directory: $(pwd)"
ls -la

echo "Generating SSL certificate and key..."
mkdir -p web/cerf
cd web/cerf

# Daha iyi bir sertifika oluştur - container'ın hostname'ini ve IP'sini ekle
HOSTNAME=$(hostname)
IP=$(hostname -i || echo "127.0.0.1")

openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes \
    -subj "/C=TR/ST=Istanbul/L=Istanbul/O=TestCase/OU=Development/CN=${HOSTNAME}" \
    -addext "subjectAltName=DNS:${HOSTNAME},DNS:localhost,IP:${IP},IP:127.0.0.1"

echo "Created certificate with:"
echo "  - Hostname: ${HOSTNAME}"
echo "  - IP: ${IP}"

cd ../../

echo "Starting Flask application with HTTPS..."
python ./web/app.py &

wait