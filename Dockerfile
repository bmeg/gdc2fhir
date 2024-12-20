FROM python:3.13

RUN apt-get update && apt-get install -y \
    libfreetype6-dev \
    libpng-dev \
    libjpeg-dev \
    zlib1g-dev \
    && apt-get clean

RUN pip install --upgrade pip

COPY . /app
WORKDIR /app

RUN pip install .

ENV PYTHONPATH="/app"

ENTRYPOINT ["/bin/bash"]
