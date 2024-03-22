FROM python

COPY . /app/
WORKDIR /app/
RUN pip install -r requirements.txt

ENV PYTHONPATH=/

CMD [ "python", "apps/app.py" ]
