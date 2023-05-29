import pyfirmata
from psychopy import core

board = pyfirmata.Arduino('/dev/ttyACM0')

motor = board.get_pin('d:12:o')
print("geht los!")
motor.write(1)
core.wait(2)
motor.write(0)
