FROM python:3.7.4-slim

WORKDIR /app
COPY Pipfile Pipfile.lock ./
RUN pip install pipenv \
    && pipenv install
COPY ./ ./
EXPOSE 80
CMD pipenv run python main.py
