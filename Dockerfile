FROM python:3.11

COPY . /app/
WORKDIR /app/

RUN pip install -r requirements.txt

ENV PYTHONPATH="/app"

CMD [ "python", "apps/app.py" ]
