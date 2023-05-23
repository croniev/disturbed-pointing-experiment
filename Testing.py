from psychopy import core
import threading
import os
import bioplux as bp
import platform
import sys


osDic = {
    "Darwin": f"MacOS/Intel{''.join(platform.python_version().split('.')[:2])}",
    "Linux": "Linux64",
    "Windows": f"Win{platform.architecture()[0][:2]}_{''.join(platform.python_version().split('.')[:2])}",
}
sys.path.append(f"PLUX-API-Python3/{osDic[platform.system()]}")
address = "BTH00:07:80:89:7F:F0"


def make_thread(data_obj):
    eeg_thread = threading.Thread(
        target=bp.exampleAcquisition,
        args=(address,  # TODO: Parameter einfügen
              data_obj))
    eeg_thread.start()
    print("Thread started")
    return eeg_thread


eeg_data_back = [[]]
make_thread(eeg_data_back)
print("Collecting...")
core.wait(3)
open("tmp", "a").close()
print(eeg_data_back)
