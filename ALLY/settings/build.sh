#!/usr/bin/env bash
# exit on error

set -o errexit

#poetry install

pip install -r requirements.txt

python manage.py collectstatic --no-input
python3 manage.py migrate


#chmod a+x build.sh