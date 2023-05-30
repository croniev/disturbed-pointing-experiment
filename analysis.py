import sys
import inspect
import os
import numpy as np
import pandas as pd
import math
import bisect
import matplotlib as plt
import seaborn as sb


def main(
        args: list
) -> None:
    if (len(args) == 0):
        print("No method to be executed was passed. Please ececute `analysis.py <args>`.")
    print("Available methods are:", [name for name, obj in inspect.getmembers(sys.modules[__name__], inspect.isfunction) if name != "main" and name != "cli"])

    for arg in args:  # Die übergebenen Methoden ausführen
        print("Executing method", arg)
        globals()[arg]()

        # show plot

        # save plot

    # Exit


# Methoden für analyse schreiben (inkl. plt.savefig())
def test():
    print("test successfull")


def cli():
    main(
        args=sys.argv[1:])


if __name__ == "__main__":
    cli()
