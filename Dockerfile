FROM python:3.9-slim

WORKDIR /app

ENV PIP_NO_CACHE_DIR 1
RUN pip install pipenv wheel

COPY Pipfile* ./
RUN pipenv install --deploy --dev
COPY . .

ENV PYTHONUNBUFFERED 1

ENV DEBUG 1
RUN pipenv run python scripts/create_testdata.py \
 && pipenv run python manage.py migrate --check
ENV DEBUG 0

CMD pipenv run python manage.py runserver 0.0.0.0:80
