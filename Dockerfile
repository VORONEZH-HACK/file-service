FROM python:3.11-bullseye

ARG WORK_DIR=/opt/mnt
ENV PYTHONPATH=$WORK_DIR

WORKDIR $WORK_DIR

COPY requirements.txt ./

RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY ./app ./app

CMD ["python", "-m", "app"]
