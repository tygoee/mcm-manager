# Testing

Tests are used to ensure the program doesn't break after something has changed. The following information is useful if you need to write tests yourself or want to run the tests.

## Information

For testing, the `unittest` library is used. Tests are made in the `tests/` directory, usually in the format of `test_(file).py`. As `src` is a package, you can import files using:

```python
from src import main
```

## Running tests

Running tests is pretty simple. As `unittest` is in the standard library, you don't need to install any additional pip libraries. To run tests, navigate to the github root directory ( `mcm-manager/` ) and run the following command:

```shell
python3 -m unittest -v
```
