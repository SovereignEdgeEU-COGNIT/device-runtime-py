# Cognit Device Runtime test
The tests are written using the pytest framework. In order to run the tests, the following command can be used:

## Run unit tests

```
cd cognit/test/unit
pytest --log-cli-level=DEBUG -s
```

# Run  integration tests

```
cd cognit/test/integration
pytest --log-cli-level=DEBUG -s
```

**NOTE**: Integration tests need a valid configuration file located in `cognit/test/config/cognit.yml` pointing to a valid provisioning engine endpoint.

