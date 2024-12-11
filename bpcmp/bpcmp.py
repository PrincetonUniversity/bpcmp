import os
import sys
import argparse
from termcolor import colored
import adios2 as ad
import numpy as np


def main():
    """
    Utility for comparing two ADIOS2 bp output files. The user specifies the file locations and
    can customize the comparison by setting verbosity levels, absolute/relative tolerances, and
    attributes/variables to ignore.

    Floating-point comparisons are performed using numpy's `allclose` function:
        np.allclose(): abs(arr1 - arr2) <= (atol + rtol * abs(arr2))

    Inspired by this gist:
        https://gist.github.com/jychoi-hpc/b4654e178edd84c9b8a2a198ab1c6c95

    Usage:
        bpcmp out1.bp out2.bp

    Options:
        -v LEVEL    Verbosity level: (0) No output, (1) Errors only, (2) All details
        -r RTOL     Relative tolerance for floating-point comparisons (default: 0.0)
        -a ATOL     Absolute tolerance for floating-point comparisons (default: 0.0)
        --ignore-atts IGNORE_ATTS   List of attributes to ignore
        --ignore-vars IGNORE_VARS   List of variables to ignore

    Example:
        bpcmp out1.bp out2.bp -v 2 -r 1e-6 -a 1e-4 --ignore-atts att1 att2 --ignore-vars var1 var2
    """

    # Print welcome message
    print(colored('bpcmp: ADIOS2 bp output comparison utility\n', attrs=['bold']))

    # Counter for the number of detected differences
    num_differences = 0

    # Argument parsing configuration
    description = 'bpcmp utility for comparing ADIOS2 bp output'
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('output1', help='Path to the first ADIOS2 bp output file')
    parser.add_argument('output2', help='Path to the second ADIOS2 bp output file')
    parser.add_argument('-r', '--rtol', help='Relative tolerance (default: 0.0)', type=float, default=0.0)
    parser.add_argument('-a', '--atol', help='Absolute tolerance (default: 0.0)', type=float, default=0.0)
    parser.add_argument('-v', '--verbose', help='Verbosity level: 0, 1, or 2 (default: 0)', type=int, default=0)
    parser.add_argument('--ignore-atts', help='Attributes to ignore', nargs='+', default=None)
    parser.add_argument('--ignore-vars', help='Variables to ignore', nargs='+', default=None)

    # Parse command-line arguments
    args = parser.parse_args()

    # Validate the paths to the output files
    if not os.path.exists(args.output1):
        print(colored(f'ERROR: Output file does not exist: {args.output1}', color='red', attrs=['bold']))
        sys.exit(1)
    output1 = args.output1

    if not os.path.exists(args.output2):
        print(colored(f'ERROR: Output file does not exist: {args.output2}', color='red', attrs=['bold']))
        sys.exit(1)
    output2 = args.output2

    # Validate and set tolerances
    if args.atol < 0.0:
        print(colored(f'ERROR: Absolute tolerance cannot be negative: {args.atol}', color='red', attrs=['bold']))
        sys.exit(1)
    atol = args.atol

    if args.rtol < 0.0:
        print(colored(f'ERROR: Relative tolerance cannot be negative: {args.rtol}', color='red', attrs=['bold']))
        sys.exit(1)
    rtol = args.rtol

    # Set verbosity level
    if args.verbose not in (0, 1, 2):
        raise argparse.ArgumentTypeError('Invalid verbosity level. Choose from: 0 (none), 1 (errors), 2 (all)')
    verbose = args.verbose

    # Copy ignore lists if provided
    ignore_atts = args.ignore_atts.copy() if args.ignore_atts else []
    ignore_vars = args.ignore_vars.copy() if args.ignore_vars else []

    # Display a summary of the inputs
    print(f'ADIOS2 bp output 1: {output1}')
    print(f'ADIOS2 bp output 2: {output2}')
    print(f'Absolute tolerance: {atol:e}')
    print(f'Relative tolerance: {rtol:e}')
    print(f'Verbose level: {verbose}')
    if ignore_atts:
        print(f'Attributes to ignore: {ignore_atts}')
    if ignore_vars:
        print(f'Variables to ignore: {ignore_vars}')
    print('')

    def compare_values(v1, v2):
        """
        Compare two values (scalars or arrays) using specified tolerances.

        Returns:
            tuple: (bool, max difference) where the bool indicates if values are equal.
        """
        # Handle scalar comparison
        if np.isscalar(v1) and np.isscalar(v2):
            return v1 == v2, abs(v2 - v1)

        # Handle array comparison
        elif isinstance(v1, np.ndarray) and isinstance(v2, np.ndarray):
            if v1.shape == v2.shape:
                return np.allclose(v1, v2, rtol=rtol, atol=atol), np.max(np.abs(v2 - v1))
            else:
                return False, None

        # Incompatible types
        return False, None

    # Open the ADIOS2 bp output
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

    # Final summary of differences
    if num_differences == 0:
        print(colored(f'{output1} and {output2} are identical', attrs=['bold']))
    else:
        print(colored(f'{num_differences} differences found between {output1} and {output2}', attrs=['bold']))

    sys.exit(0 if num_differences == 0 else 1)
