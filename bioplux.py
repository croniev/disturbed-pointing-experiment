import plux
import os


class NewDevice(plux.SignalsDev):
    def __init__(self, address, data_obj):
        plux.MemoryDev.__init__(address)
        self.data_obj = data_obj

    def onRawFrame(self, nSeq, data):
        print(data)
        self.data_obj.append(data)  # TODO: was genau hier?

        if not os.path.isfile("tmp"):  # If file is present stop recording
            os.remove("tmp")
            return True
        return False


def exampleAcquisition(address, data_obj):  # time acquisition for each frequency
    device = NewDevice(address, data_obj)
    device.start(1000, 0x01, 16)
    device.loop()  # calls device.onRawFrame until it returns True
    device.stop()
    device.close()
