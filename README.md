# Mapping finite element data between meshes

[![travis](https://img.shields.io/travis/tianyikillua/pymapping.svg?style=flat-square)](https://travis-ci.org/tianyikillua/pymapping)
[![codecov](https://img.shields.io/codecov/c/github/tianyikillua/pymapping.svg?style=flat-square)](https://codecov.io/gh/tianyikillua/pymapping)
[![PyPi Version](https://img.shields.io/pypi/v/pymapping.svg?style=flat-square)](https://pypi.org/project/pymapping)

This package is a handy Python (re-)wrapper of [MEDCoupling](https://docs.salome-platform.org/latest/dev/MEDCoupling/developer/index.html). It can be used to transfer finite element data defined on nodes (P1 fields) or on cells (P0 fields) between two [meshio](https://github.com/nschloe/meshio)-compatible meshes.

<p align="center">
  <img src="https://user-images.githubusercontent.com/4027283/60191481-ab3af580-9834-11e9-8f55-e02f2bd6c0fa.png" width="400">
</p>

Some notebook examples can be found in `examples`.

Documentation is available [here](https://pymapping.readthedocs.io).

### Installation

To install `pymapping`, you are invited to use `pip` and its associated options
```
pip install -U pymapping
```

The MEDCoupling library is a strong dependency of this package. Currently by installing via the previous `pip` command it will automatically install the [medcoupling](https://github.com/tianyikillua/medcoupling) Python package (a repackaging of the official library), which requires a Windows / Linux system and a Python 3.6 environment.

### Testing

To run the `pymapping` unit tests, check out this repository and type
```
pytest
```

### License

`pymapping` is published under the [MIT license](https://en.wikipedia.org/wiki/MIT_License).
