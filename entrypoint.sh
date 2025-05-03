#!/bin/bash

echo "Working directory: $(pwd)"
ls -la

echo "Generating SSL certificate and key..."
mkdir -p web/cerf
cd web/cerf
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes \
    -subj "/C=US/ST=SomeState/L=SomeCity/O=SomeOrganization/OU=SomeOrgUnit/CN=localhost"
cd ../../

echo "Starting Flask application with HTTPS..."
python ./web/app.py &

wait