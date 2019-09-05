FROM python:3.7.4-slim

WORKDIR /api
COPY Pipfile Pipfile.lock ./
RUN pip install pipenv \
    && pipenv install --dev
COPY ./ ./
EXPOSE 80
CMD pipenv run python app/main.py
