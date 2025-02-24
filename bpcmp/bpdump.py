import os
import argparse
from importlib import metadata
import adios2 as ad
from collections import OrderedDict


def main():
    """
    Utility to dump the content of an ADIOS2 bp output.

    Usage:
        bpdump out.bp
    """

    # Print welcome message
    print(f"bpdump: ADIOS2 bp dump utility, v{metadata.version('bpcmp')}\n")

    # Define arguments
    description = "bpdump utility for dumping ADIOS2 bp output content"
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("bpout", help="Path to the ADIOS2 bp output file")

    # Parse command line arguments
    args = parser.parse_args()

    # Check if the output file exists
    if not os.path.exists(args.bpout):
        raise FileNotFoundError(f"Output file does not exist: {args.bpout}")

    # Open the ADIOS2 bp output using a context manager
    with ad.FileReader(args.bpout) as bpout:
        bpdict = {}

        # Collect attributes into the bp dictionary
        attributes = bpout.available_attributes()
        for attribute, attr_info in attributes.items():
            bpdict[attribute] = attr_info["Value"]

        # Collect variables into the bp dictionary
        for variable in bpout.available_variables():
            bpdict[variable] = bpout.read(variable)

    # Convert the bp dictionary into an ordered dict
    ordered_dict = OrderedDict(sorted(bpdict.items()))

    # Dump the bp output file to the screen
    for key, item in ordered_dict.items():
        # Skip displaying 'description' and 'units' entries directly
        if any(val in key for val in ["description", "units"]):
            continue

        # Display associated 'description' if it exists
        if key + "/description" in ordered_dict:
            print(f"{key + '/description':32}{ordered_dict[key + '/description']}")

        # Display associated 'units' if it exists
        if key + "/units" in ordered_dict:
            print(f"{key + '/units':32}{ordered_dict[key + '/units']}")

        # Display the actual key and value
        print(f"{key:32}{item}\n")

        # Print an extra newline for readability if 'units' are present
        if "units" in key:
            print("")


if __name__ == "__main__":
    main()
