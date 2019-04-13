FROM python:3.7-slim-stretch

RUN apt update && \
    apt install -y git && \
    cd /usr/src/ && \
    git clone https://github.com/n0mjs710/dmr_utils3 && \
    cd /usr/src/dmr_utils3 && \
    ./install.sh && \
    rm -rf /var/lib/apt/lists/* && \
    cd /opt && \
    rm -rf /usr/src/dmr_utils3 && \
    git clone https://github.com/n0mjs710/hblink3

RUN cd /opt/hblink3/ && \
    sed -i s/.*python.*//g  requirements.txt && \
    pip install --no-cache-dir -r requirements.txt


ADD entrypoint /entrypoint

RUN adduser -u 54000 radio && \
    adduser radio radio && \
    chmod 755 /entrypoint && \
    chown radio:radio /entrypoint && \
    chown radio /opt/hblink3

RUN chmod 755 /entrypoint

USER radio 
EXPOSE 54000

ENTRYPOINT [ "/entrypoint" ]
