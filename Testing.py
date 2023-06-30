import plux
from psychopy import core
import threading
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import collections
import numpy as np


class MyBioplux(plux.SignalsDev):
    def __init__(self, address):
        plux.MemoryDev.__init__(address)
        # self.bucket = None
        # self.timer = None

    def onRawFrame(self, nSeq, data):
        print(*data)
        global eeg_data
        eeg_data.popleft()
        eeg_data.append(*data)
        # print(float(*data))

        # if self.bucket:
        #    eeg_data[self.bucket].popleft()
        #    eeg_data[self.bucket].append(float(*data))

        #    eeg_data[str(self.bucket + "_timestamps")].append(self.timer.getTime())
        return False

    # def collect(self, bucket, timer):
    #    global eeg_data
    #    self.bucket = bucket
    #    if bucket:
    #        eeg_data[bucket] = []
    #        eeg_data[str(bucket + "_timestamps")] = []
    #    self.timer = timer


def my_funct(i):
    ax.cla()
    lst = list(eeg_data)
    # n = 20
    interpol = lst
    # interpol = [x for x in eeg_data if x > 100]
    # interpol = [max(interpol[x:x + n]) for x in range(0, len(interpol))]
    # interpol = [interpol[i] for i in range(n, len(interpol) - n) if abs(interpol[i] - np.mean(interpol[i-n:i+n])) < 100]
    # interpol = [np.mean(interpol[x:x+20]) for x in range(0, len(interpol))]

    # interpol = np.cumsum(np.insert(interpol, 0, 0))
    # interpol = (interpol[n:] - interpol[:-n]) / float(n)

    ax.plot(interpol)
    # ax.scatter(len(eeg_data["eeg_back"])-1, eeg_data["eeg_back"][-1])
    ax.set_ylim(0, 30000)


# Before collecting
# eeg_data = {"eeg_back": collections.deque(np.zeros(300)), "eeg_start": [], "eeg_forward": [], "eeg_pr": [], "eeg_back_timestamps": [], "eeg_start_timestamps": [], "eeg_forward_timestamps": [], "eeg_pr_timestamps": []}
eeg_data = collections.deque(np.zeros(10000))

device = MyBioplux("BTH00:07:80:89:7F:F0")

device.start(1000, 0x01, 16)
t = threading.Thread(target=device.loop)
t.setDaemon(True)
t.start()
print("Thread started. Collecting...")

# During collection
fig = plt.figure(figsize=(6, 6), facecolor='#DEDEDE')
ax = plt.subplot(111)
ax.set_facecolor('#DEDEDE')

# device.collect("eeg_back", core.Clock())

ani = FuncAnimation(fig, my_funct, interval=1)
plt.show()


# TODO: prop report testen
# Methode schreiben die auch collection beeinflussen und danach aus datan heraus lesen kann

# After collecting
device.interrupt()
device.stop()
device.close()
