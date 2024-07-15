FROM python:3.12

RUN pip3 install --upgrade pip

COPY . /app
WORKDIR /app
RUN pip install .

ENV PYTHONPATH="$PYTHONPATH:/app"
ENTRYPOINT ["/bin/bash"]