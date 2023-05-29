import plux
from psychopy import core
import threading


class MyBioplux(plux.SignalsDev):
    def __init__(self, address):
        plux.MemoryDev.__init__(address)
        self.bucket = None
        self.timer = None

    def onRawFrame(self, nSeq, data):
        global eeg_data
        if self.bucket:
            eeg_data[self.bucket].append(float(*data))
            eeg_data[str(self.bucket + "_timestamps")].append(self.timer.getTime())
        return False

    def collect(self, bucket, timer):
        global eeg_data
        self.bucket = bucket
        if bucket:
            eeg_data[bucket] = []
            eeg_data[str(bucket + "_timestamps")] = []
        self.timer = timer


# Before collecting
eeg_data = {"eeg_back": [], "eeg_start": [], "eeg_forward": [], "eeg_pr": [], "eeg_back_timestamps": [], "eeg_start_timestamps": [], "eeg_forward_timestamps": [], "eeg_pr_timestamps": []}
device = MyBioplux("BTH00:07:80:89:7F:F0")
device.start(1000, 0x01, 16)
threading.Thread(target=device.loop).start()
print("Thread started. Collecting...")

# During collection
device.collect("eeg_back", core.Clock())
core.wait(1)
device.collect("eeg_start", core.Clock())
core.wait(1)
device.collect(None, None)
core.wait(1)
device.collect("eeg_forward", core.Clock())
core.wait(1)

# TODO: prop report testen
# Methode schreiben die auch collection beeinflussen und danach aus datan heraus lesen kann

# After collecting
device.interrupt()
device.stop()
device.close()
