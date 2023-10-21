'''
This is some example code for how to read data from a bioPLUX device connected via bluetooth.
Make sure that you have the required plux package in the same folder (https://github.com/pluxbiosignals/python-samples/tree/master/PLUX-API-Python3).
'''

import plux
import threading
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import collections
import numpy as np


class MyBioplux(plux.SignalsDev):
    def __init__(self, address):
        plux.MemoryDev.__init__(address)

    def onRawFrame(self, nSeq, data):
        # print(*data)
        global eeg_data
        eeg_data.popleft()
        eeg_data.append(*data)
        return False


def my_funct(i):
    ax.cla()
    ax.plot(list(eeg_data))
    ax.set_ylim(0, 30000)


# Before collecting
eeg_data = collections.deque(np.zeros(10000))

device = MyBioplux("BTH00:07:80:89:7F:F0")  # TODO: check on bioPLUX device what the MAC address is

device.start(1000, 0x01, 16)
t = threading.Thread(target=device.loop)
t.setDaemon(True)
t.start()
print("Thread started. Collecting...")

# During collection
fig = plt.figure(figsize=(6, 6), facecolor='#DEDEDE')
ax = plt.subplot(111)
ax.set_facecolor('#DEDEDE')

ani = FuncAnimation(fig, my_funct, interval=1)
plt.show()

# After collecting
device.interrupt()
device.stop()
device.close()
