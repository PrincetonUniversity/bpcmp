import os
import sys
import argparse
from termcolor import colored
import adios2 as ad
import numpy as np


def main():
    """
    Utility which allows for the comparison of two ADIOS2 bp output. The user
    must specify the location of the output and can choose for verbose output,
    set the absolute and relative tolerances for float type variables, and
    specify attributes and variables to ignore.

    Inspired by this gist:
        https://gist.github.com/jychoi-hpc/b4654e178edd84c9b8a2a198ab1c6c95

    Floating point comparison done using allclose from numpy:
        np.allclose(): absolute(arr1 - arr2) <= (atol + rtol * absolute(arr2))

    Usage:
        bpcmp out1.bp out2.bp

        Arguments:
        -v LEVEL    Use for verbose output of comparison: (0,1,2) to report (nothing, errors only, everything)
        -r RTOL     Set the relative tolerance when comparing float variables (default is zero)
        -a ATOL     Set the absolute tolerance when comparing float variables (default is zero)
        --ignore-atts IGNORE_ATTS   Provide list of attributes to ignore
        --ignore-vars IGNORE_VARS   Provide list of variables to ignore

        bpcmp out1.bp out.bp -v -r 0.000001 -a 0.0001 --ignore-atts att1 att2 --ignore-vars var1 var2
    """

    # Print welcome message
    print(colored('bpcmp: ADIOS2 bp output comparison utility', attrs=['bold']))

    # Inputs
    output1 = None
    output2 = None
    verbose = 0  # Verbose output level (write out differences)
    rtol = 0.0  # relative tolerance
    atol = 0.0  # absolute tolerance
    ignore_atts = []  # List of attributes to ignore
    ignore_vars = []  # List of variables to ignore

    # Count number of differences
    num_differences = 0

    # Define arguments
    description = 'bpcmp utility for comparing ADIOS2 bp output'
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('output1',
                        help='ADIOS2 bp output number 1',
                        default=None)
    parser.add_argument('output2',
                        help='ADIOS2 bp output number 2',
                        default=None)
    parser.add_argument('-r', '--rtol',
                        help='relative tolerance (default is zero)',
                        type=float,
                        default=0.0)
    parser.add_argument('-a', '--atol',
                        help='absolute tolerance (default is zero)',
                        type=float,
                        default=0.0)
    parser.add_argument('-v', '--verbose',
                        help='verbose output: (0,1,2) to report (nothing, errors only, everything)',
                        type=int,
                        default=0)
    parser.add_argument('--ignore-atts',
                        help='List of attributes to ignore',
                        nargs='+',
                        default=None)
    parser.add_argument('--ignore-vars',
                        help='List of variables to ignore',
                        nargs='+',
                        default=None)

    # Parse command line arguments
    args = parser.parse_args()

    print('')
    if os.path.exists(args.output1):
        output1 = args.output1
    else:
        print(colored(f'ERROR: output does not exist, {args.output1}\n', color='red', attrs=['bold']))
        sys.exit(1)

    if os.path.exists(args.output2):
        output2 = args.output2
    else:
        print(colored(f'ERROR: output does not exist, {args.output2}\n', color='red', attrs=['bold']))
        sys.exit(1)

    if args.atol < 0.0:
        print(colored(f'ERROR: absolute tolerance cannot be negative {args.atol}\n', color='red', attrs=['bold']))
        sys.exit(1)
    atol = args.atol

    if args.rtol < 0.0:
        print(colored(f'ERROR: relative tolerance cannot be negative {args.atol}\n', color='red', attrs=['bold']))
        sys.exit(1)
    rtol = args.rtol

    if args.verbose is None:
        verbose = 1
    elif int(args.verbose) < 0 or int(args.verbose) > 2:
        raise argparse.ArgumentTypeError('Invalid verbose level: (0,1,2) to report (nothing, errors only, everything)')
    else:
        verbose = int(args.verbose)

    if args.ignore_atts:
        ignore_atts = args.ignore_atts.copy()

    if args.ignore_vars:
        ignore_vars = args.ignore_vars.copy()

    # Summarize inputs to the console
    print(f'ADIOS2 bp output 1: {output1}')
    print(f'ADIOS2 bp output 2: {output2}')
    print(f'Absolute tolerance: {atol:e}')
    print(f'Relative tolerance: {rtol:e}')
    print(f'Verbose output level: {verbose}')
    if len(ignore_atts) > 0:
        print(f'Ignored attributes: {ignore_atts}')
    if len(ignore_vars) > 0:
        print(f'Ignored variables: {ignore_vars}')
    print('')

    def compare_values(v1, v2):
        """Perform comparison of two ADIOS 2 values which could be scalars or arrays"""

        if np.isscalar(v1) and np.isscalar(v2):
            return v1 == v2, abs(v2 - v1)
        elif not np.isscalar(v1) and not np.isscalar(v2):
            if v1.shape == v2.shape:
                return (np.allclose(v1, v2, rtol=rtol, atol=atol), np.max(v2 - v1))
            else:
                return False, None
        else:
            return False, None

    # Open the ADIOS2 bp output (already check for existence in init)
    f1 = ad.FileReader(output1)
    f2 = ad.FileReader(output2)

    # Compare attributes
    for v in f1.available_attributes():
        # Skip current attribute if in the ignore list
        if v in ignore_atts:
            continue

        # Read attribute from output 1
        v1 = f1.available_attributes()[v]['Value']

        # Read attribute from output 2, report as difference if attribute does not exist
        try:
            v2 = f2.available_attributes()[v]['Value']
        except Exception:
            num_differences += 1
            if verbose:
                att = colored(f'{v}', color='yellow', attrs=['bold'])
                msg = (colored('NOATT: ', color='yellow', attrs=['bold']) +
                       f'Attribute {att} found in {output1} but not {output2}')
                print(msg)
            continue

        # Compare the attributes based on types
        if f1.available_attributes()[v]['Type'] == 'string':
            if v1 != v2:
                num_differences += 1
                if verbose:
                    att = colored(f'{v}', color='red', attrs=['bold'])
                    msg = (colored('DIFF:  ', color='red', attrs=['bold']) +
                           f'Attribute {att} has differences: ' +
                           f'{output1} = {v1} and ' +
                           f'{output2} = {v2}')
                    print(msg)
            else:
                if verbose == 2:
                    att = colored(f'{v}', color='blue', attrs=['bold'])
                    msg = (colored('PASS:  ', color='blue', attrs=['bold']) +
                           f'Attribute {att} is the same in both outputs')
                    print(msg)
        else:
            # Re-reading input as integer or float (could be scalars or lists)
            v1 = f1.read_attribute(v)
            v2 = f2.read_attribute(v)
            same, maxdiff = compare_values(v1, v2)
            if maxdiff is None:
                num_differences += 1
                if verbose:
                    att = colored(f'{v}', color='red', attrs=['bold'])
                    msg = (colored('ERROR: ', color='red', attrs=['bold']) +
                           f'Attribute {att} has inconsistent types: ' +
                           f'{output1} = {v1} and ' +
                           f'{output2} = {v2}')
                    print(msg)
            elif not same:
                num_differences += 1
                if verbose:
                    att = colored(f'{v}', color='red', attrs=['bold'])
                    msg = (colored('DIFF:  ', color='red', attrs=['bold']) +
                           f'Attribute {att} has differences, max difference: ' +
                           f'{maxdiff}')
                    print(msg)
            else:
                if verbose == 2:
                    msg = ''
                    att = colored(f'{v}', color='blue', attrs=['bold'])
                    msg = (colored('PASS:  ', color='blue', attrs=['bold']) +
                           f'Attribute {att} is the same in both outputs')
                    print(msg)

    # Compare variables (note that in ADIOS 2, variables cannot be strings)
    for v in f1.available_variables():
        # Skip current variable if in the ignore list
        if v in ignore_vars:
            continue

        # Read variable from output 1
        v1 = f1.read(v)

        # Read attribute from output 2, report as difference if attribute does not exist
        try:
            v2 = f2.read(v)
        except Exception:
            num_differences += 1
            if verbose:
                var = colored(f'{v}', color='yellow', attrs=['bold'])
                msg = (colored('NOVAR: ', color='yellow', attrs=['bold']) +
                       f'Variable {var} found in {output1} but not {output2}')
                print(msg)
            continue

        same, maxdiff = compare_values(v1, v2)
        if maxdiff is None:
            num_differences += 1
            if verbose:
                var = colored(f'{v}', color='red', attrs=['bold'])
                msg = (colored('ERROR: ', color='red', attrs=['bold']) +
                       f'Variable {var} has inconsistent shapes: ' +
                       f'{output1} = {v1.shape} and ' +
                       f'{output2} = {v2.shape}')
                print(msg)
        elif not same:
            num_differences += 1
            if verbose:
                var = colored(f'{v}', color='red', attrs=['bold'])
                msg = (colored('DIFF:  ', color='red', attrs=['bold']) +
                       f'Variable {var} has differences, max difference: ' +
                       f'{maxdiff}')
                print(msg)
        else:
            if verbose == 2:
                msg = ''
                var = colored(f'{v}', color='blue', attrs=['bold'])
                msg = (colored('PASS:  ', color='blue', attrs=['bold']) +
                       f'Variable {var} is the same in both outputs')
                print(msg)

    # Close the ADIOS2 output
    f1.close()
    f2.close()

    # Report the differences
    if num_differences == 0:
        print(colored(f'{output1} and {output2} are identical', attrs=['bold']))
        sys.exit(0)
    else:
        print(colored(f'{num_differences} differences found between {output1} and {output2}', attrs=['bold']))
        sys.exit(1)
