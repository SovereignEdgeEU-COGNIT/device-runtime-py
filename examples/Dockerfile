FROM python:3.10.6
RUN mkdir /cognit
WORKDIR /cognit
COPY . .
RUN pip install -r requirements.txt
RUN python setup.py sdist   
RUN pip install dist/cognit-0.0.0.tar.gz

ENTRYPOINT ["python", "examples/minimal_offload_sync.py"]
