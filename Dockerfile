FROM python:3.8.3-slim-buster

RUN apt-get update && apt-get -y install libpq-dev gcc apt-transport-https && pip install psycopg2 \
    && pip install --upgrade pip && mkdir -pv /var/{log,run}/gunicorn/ && mkdir -pv /home/app \
    && apt-get update && apt-get -y install tesseract-ocr && apt-get update && apt-get install -y libgl1-mesa-glx  \
    && apt-get install -y poppler-utils

ENV PROJECT_DIR=/home/app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONBUFFERED=1

WORKDIR $PROJECT_DIR

COPY  requirements.txt $PROJECT_DIR/requirements.txt
RUN chmod +x $PROJECT_DIR/requirements.txt
RUN python3 -m pip install -r requirements.txt

# copy project
COPY . $PROJECT_DIR
COPY entrypoint.sh ${PROJECT_DIR}/entrypoint.sh
RUN chmod +x ${PROJECT_DIR}/entrypoint.sh




COPY . $PROJECT_DIR


ENTRYPOINT ["/home/app/entrypoint.sh"]
