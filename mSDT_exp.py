"""
Load an image, save to JPEG, show with PsychoPy and
collect a key response.

Run from the command line, from the /src directory. Example:

python basic_demo.py -d "jpg" -p 50
python basic_demo.py -d "blur" -p 2

For more options type

python basic_demo.py --help
"""

from pathlib import Path
import os
from PIL.Image import blend
import numpy as np
import pandas as pd
import random
from datetime import datetime
import sys
import click
from psychopy import prefs, monitors
from psychopy.visual.window import Window
from psychopy.event import Mouse
from psychopy import core

from psychopy.tools import monitorunittools
import math
#from pyrsistent import T

# to avoid bug on windows (https://www.psychopy.org/troubleshooting.html#errors-with-getting-setting-the-gamma-ramp)
prefs.general["gammaErrorPolicy"] = "warn"

size = 250

from psychopy import core, event, visual
#from gen_pink_noise import pink_noise_image
#from scipy import fftpack
# https://www.psychopy.org/general/rendering.html#blendmode

def main(
    screen: int = 0,
    debug: bool = False,
) -> None:
    # Open a PsychoPy window, show the image, collect a keypress, close.
    win = visual.Window(
        #(500, 500),  # arbitrary if we're doing fullscreen
        screen=screen,
        units="pix",
        allowGUI=True,
        fullscr=not(debug), # FINAL: debug auf False setzen
        blendMode="add"
    )

    hit_radius = 30 # TODO: hit_radius als parameter
    n_trials = 3 # TODO: als parameter

    instruction_text = visual.TextStim(
        win,
        units="norm",
        text=(
            "Press space to continue."
        ),
        wrapWidth=0.9,
        height=0.05,
    )
   
    instruction_text.draw()
    win.setMouseVisible(False)
    win.flip()
    event.waitKeys(keyList=["space"])

    mouse = Mouse(visible=False, win = win)
    mouse.clickReset()

    win.flip()
    core.wait(0.3)
    
    for trial in range(n_trials):
        # Setup trial
        completed = False
        xoff = 0
        yoff = 1
        mouse.setPos([0,-200])
        target_pos = (0,200) # TODO: varying pos?
        debug_circle = new_circle(win,target_pos,color=(50,0,200))
        debug_circle.setRadius(hit_radius)
        target_circle = new_circle(win,target_pos,color=(200,0,50))

        while(not completed):
            mouse_pos = mouse.getPos()
            dist = math.dist(mouse_pos, target_pos)
            xoff = max(0, 0.01 * (400-dist))
            new_mouse_pos = [mouse_pos[0]+xoff,mouse_pos[1]+yoff]
            mouse.setPos(new_mouse_pos)

            # Draw Stuff
            new_circle(win,new_mouse_pos).draw()
            debug_circle.draw()
            target_circle.draw()
            win.flip()

            # Breakout condition
            if dist < hit_radius:
                completed = True
            core.wait(0.005)


    # END SESSION
    win.setMouseVisible(True)
    win.close()
    core.quit()

def new_circle(win, pos: tuple, color=(255,255,255)):
    new_circ=visual.Circle(
            win,
            radius = 15,
            pos = pos,
            opacity = 1,
            fillColor = color,
            colorSpace = 'rgb255')
    return new_circ

@click.command()

@click.option(
    "--screen",
    default=0,
    type=int,
    show_default=True,
    help="Use integers > 0 to specify other monitors. See PsychoPy's visual.Window()",
)
@click.option(
    "--debug",
    default=False,
    is_flag=True,
    show_default=True,
    help="Pass to enable debug mode (disable fullscreen, increase logging level)",
)
def cli(screen: int, debug: bool):
    main(
        screen=screen,
        debug=debug,
    )


if __name__ == "__main__":
    cli()
