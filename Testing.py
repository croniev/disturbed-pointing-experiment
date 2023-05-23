from psychopy import core
import threading
import os
import bioplux as bp


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
