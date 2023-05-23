from psychopy import core
import threading
import bioplux as bp

address = "BTH00:07:80:89:7F:F0"


def make_thread(data_obj):
    device = bp.MyBioplux(address)
    eeg_thread = threading.Thread(
        target=bp.exampleAcquisition,
        args=(device))
    eeg_thread.start()
    print("Thread started")
    return device


eeg_data_back = [[]]
device_back = make_thread(eeg_data_back)
print("Collecting...")
core.wait(3)
device_back.interrupt()
print(eeg_data_back)
