# Mapping finite element data between meshes

[![travis](https://img.shields.io/travis/tianyikillua/pymapping.svg?style=flat-square)](https://travis-ci.org/tianyikillua/pymapping)
[![codecov](https://img.shields.io/codecov/c/github/tianyikillua/pymapping.svg?style=flat-square)](https://codecov.io/gh/tianyikillua/pymapping)
[![PyPi Version](https://img.shields.io/pypi/v/pymapping.svg?style=flat-square)](https://pypi.org/project/pymapping)

This package is a handy Python (re-)wrapper of [MEDCoupling](https://docs.salome-platform.org/latest/dev/MEDCoupling/developer/index.html). It can be used to transfer finite element data defined on nodes (P1 fields) or on cells (P0 fields) between two [meshio](https://github.com/nschloe/meshio)-compatible meshes.

<p align="center">
  <img src="https://user-images.githubusercontent.com/4027283/60191481-ab3af580-9834-11e9-8f55-e02f2bd6c0fa.png" width="500">
</p>

Some notebook examples can be found in `examples`.

Documentation is available [here](https://pymapping.readthedocs.io).

### Installing MEDCoupling

Before using this package, you need to install MEDCoupling. Currently the 9.3.0 version only supports Python 3.6 and not Python 3.7.

1. Download and extract the source package from [salome-platform.org](http://files.salome-platform.org/Salome/other/medCoupling-9.3.0.tar.gz)
2. You will obtain two folders: `CONFIGURATION_9.3.0` and `MEDCOUPLING-9.3.0`, enter `MEDCOUPLING-9.3.0` and using `cmake` to build/install

```
mkdir build
cd build
cmake -DCONFIGURATION_ROOT_DIR=../../CONFIGURATION_9.3.0 -DCMAKE_INSTALL_PREFIX=[TO BE SPECIFIED] -DPYTHON_ROOT_DIR=[TO BE SPECIFIED] -DMEDCOUPLING_MICROMED=ON -DMEDCOUPLING_BUILD_DOC=OFF -DMEDCOUPLING_ENABLE_PARTITIONER=OFF -DMEDCOUPLING_PARTITIONER_SCOTCH=OFF -DMEDCOUPLING_PARTITIONER_METIS=OFF -DMEDCOUPLING_BUILD_TESTS=OFF -DMEDCOUPLING_ENABLE_RENUMBER=OFF -DMEDCOUPLING_WITH_FILE_EXAMPLES=OFF ..
cmake --build . --config Release --target INSTALL
```

For Windows users, the building has been tested with the latest Visual Studio 2019, with `-G "Visual Studio 16 2019" -A x64`. If you are using `conda` with `py36` a Python 3.6 `env`, you can

1. Specify `DCMAKE_INSTALL_PREFIX=...\Miniconda3\envs\py36\Library`
2. Specify `DPYTHON_ROOT_DIR=...\Miniconda3\envs\py36`
3. After installation, move files in `py36\Library\lib\python3.6\site-packages` to `py36\Lib\site-packages`, and move `.dll` files in `py36\Library\lib` to `py36\Library\bin`

To assure that MEDCoupling is well installed, try importing it in your Python
```
import medcoupling  # should not raise error
```

### Testing

To run the `pymapping` unit tests, check out this repository and type
```
pytest
```

### License

`pymapping` is published under the [MIT license](https://en.wikipedia.org/wiki/MIT_License).
