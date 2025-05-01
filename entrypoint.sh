!/bin/bash

echo "Working directory: $(pwd)"
ls -la

./cpp/server &

python ./web/app.py &

wait
