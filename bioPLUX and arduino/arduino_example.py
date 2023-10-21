import pyfirmata
from psychopy import core
import platform

if platform.system() == 'Windows':
    board = pyfirmata.Arduino('COM5', baudrate=57600)
else:
    board = pyfirmata.Arduino('/dev/ttyACM0')

motor = board.get_pin('d:12:o')
print("geht los!")
motor.write(1)
core.wait(2)
motor.write(0)
