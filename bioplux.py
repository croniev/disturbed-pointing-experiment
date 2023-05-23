import plux


class MyBioplux(plux.SignalsDev):
    def __init__(self, address):
        plux.MemoryDev.__init__(address)
        self.saved_data = []

    def onRawFrame(self, nSeq, data):
        self.saved_data.append(float(*data))  # TODO: was genau hier?
        return False

    def onInterrupt(self, data_obj):
        data_obj.append(self.saved_data)
        return True


def exampleAcquisition(device):
    device.start(1000, 0x01, 16)
    device.loop()  # calls device.onRawFrame until it returns True
    device.stop()
    device.close()
