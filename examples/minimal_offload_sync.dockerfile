FROM python:3.10.6
# Create /cognit folder and convert it in the default work directory
RUN mkdir /cognit
WORKDIR /cognit
# Copy repository inside the image 
COPY . .
# Generate cognit library
RUN pip install -r requirements.txt \
    && python setup.py sdist  \
    && pip install dist/cognit-0.0.0.tar.gz
# Run python example script when the image is executed
ENTRYPOINT ["python3", "examples/minimal_offload_sync.py"]
