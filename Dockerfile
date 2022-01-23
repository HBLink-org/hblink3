FROM python:3.9-alpine

COPY entrypoint /entrypoint

RUN adduser -D -u 54000 radio && \
        apk update && \
        apk add git gcc musl-dev && \
        cd /opt && \
        git clone https://github.com/ShaYmez/hblink3 && \
        cd /opt/hblink3 && \
        pip install --no-cache-dir -r requirements.txt && \
        apk del git gcc musl-dev && \
        chown -R radio: /opt/hblink3

USER radio

ENTRYPOINT [ "/entrypoint" ]
