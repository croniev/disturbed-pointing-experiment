import pyfirmata
from psychopy import core

board = pyfirmata.Arduino('/dev/ttyACM0')  # TODO: dev name

it = pyfirmata.util.Iterator(board)
it.start()

motor = board.get_pin('d:12:o')
core.wait(0.2)
motor.write(1)
core.wait(0.2)
motor.write(0)
