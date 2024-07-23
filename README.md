# bpcmp

Utility which allows for the comparison of two [ADIOS2](https://adios2.readthedocs.io/en/latest/index.html) bp output. The user must specify the location of the output and can choose for verbose output, set the absolute and relative tolerances for float type variables, and specify attributes and variables to ignore.

Inspired by this [gist](https://gist.github.com/jychoi-hpc/b4654e178edd84c9b8a2a198ab1c6c95).

Floating point comparison done using numpy [allclose](https://numpy.org/doc/stable/reference/generated/numpy.allclose.html).

Install with pip:

```
pip install -e .
```

Usage:

```
bpcmp out1.bp out2.bp
```

All of the arguments are optional.

| Argument                  | Description                                                                 |
| :------------------------ | :-------------------------------------------------------------------------- |
| -v                        | Use for verbose output of comparison                                        |
| -r RTOL                   | Set the relative tolerance when comparing float variables (default is zero) |
| -a ATOL                   | Set the absolute tolerance when comparing float variables (default is zero) |
| --ignore-atts IGNORE_ATTS | Provide list of attributes to ignore                                        |
| --ignore-vars IGNORE_VARS | Provide list of variables to ignore                                         |

```
bpcmp out1.bp out.bp -v -r 0.000001 -a 0.0001 --ignore-atts att1 att2 --ignore-vars var1 var2
```
