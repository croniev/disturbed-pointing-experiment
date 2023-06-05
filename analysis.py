import sys
import inspect
import os
import numpy as np
import pandas as pd
import math
import bisect
import matplotlib as plt
import seaborn as sb

# Load data
# To know how many datasets we have (assuming that if usr_data.csv is present so are usr_1_questionnaire, usr_2_questionnaire, usr_beginning and usr_ending)
n_users = len([name for name in os.listdir('.') if os.path.isfile(name) and 'data' in name])
# quest_1 = [pd.read_csv(str(usr + "_1_questionnaire.csv")) for usr in range(n_users)]
# quest_2 = [pd.read_csv(str(usr + "_2_questionnaire.csv")) for usr in range(n_users)]
# data = [pd.read_csv(str(usr + "_data.csv")) for usr in range(n_users)]
beginning = [pd.read_csv(str(usr + "_beginning.csv")) for usr in range(n_users)]
# ending = [pd.read_csv(str(usr + "_ending.csv")) for usr in range(n_users)]


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
