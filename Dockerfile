###############################################################################
#   Copyright (C) 2024 Shane aka, ShaYmez <support@gb7nr.co.uk>
#   Version 2.0.2
###############################################################################

FROM python:alpine3.20

RUN adduser -D -u 54000 radio

WORKDIR /hblink3

# Install build dependencies
RUN apk add --no-cache git gcc musl-dev libffi-dev openssl-dev cargo

# Copy only requirements first for better layer caching
COPY requirements.txt .

RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Remove build dependencies
RUN apk del git gcc musl-dev libffi-dev openssl-dev cargo

# Copy the application code
COPY . .

RUN chown -R radio /hblink3

COPY entrypoint /entrypoint
RUN chmod +x /entrypoint

USER radio

ENTRYPOINT ["/entrypoint"]
