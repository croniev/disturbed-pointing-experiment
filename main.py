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
    distortion: str = "random"
) -> None:
    # Open a PsychoPy window, show the image, collect a keypress, close.
    win = visual.Window(
        #(500, 500),  # arbitrary if we're doing fullscreen
        screen=screen,
        units="pix",
        allowGUI=True,
        fullscr=not(debug), # FINAL: debug auf False setzen
    )

    hit_radius = 20 # TODO: hit_radius als parameter
    n_trials = 20 # TODO: als parameter
    spawn = [0,-300] # TODO: variierbar
    target_options = [230,270,320]

    instruction_text = visual.TextStim(
        win,
        units="norm",
        text=(
            "During the experiment, press Q to quit. \nPress space to continue."
        ),
        wrapWidth=0.9,
        height=0.05,
    )
   
    instruction_text.draw()
    win.setMouseVisible(False)
    win.flip()
    pressed_key = event.waitKeys(keyList=["space","q"])

    if pressed_key[0][0] == "q":
        win.setMouseVisible(True)
        win.close()
        core.quit()

    mouse = Mouse(visible=False, win = win)
    mouse.clickReset()

    win.flip()
    core.wait(0.3)
    
    for trial in range(n_trials):
        # Setup trial
        completed = False
        mouse.setPos(spawn)
        target_pos = [0,random.choice(target_options)]
        if distortion == "random":
            dist_type = np.random.choice(["none","straight","rotate","repell","burst"],p=[0.8,0.05,0.05,0.05,0.05])
        else:
            dist_type = distortion
        # Setup burst distort
        burst_time = 0.5
        burst_dur = 0.2
        burst_force = -10 # Horizontal burst force
        timer = core.Clock()

        target_circle = new_circle(win,target_pos,r=20,color=(200,0,50))

        while(not completed):
            mouse_pos = mouse.getPos()

            # Distortions
            if (dist_type == "none"):
                new_mouse_pos = (mouse_pos[0],mouse_pos[1])
            if (dist_type == "straight"):
                new_mouse_pos = (0,mouse_pos[1])
            if (dist_type == "rotate"):
                new_mouse_pos = rotate_point(mouse_pos, 30, origin=(0,-200)) # TODO: make parameter
            if (dist_type == "repell"):
                new_mouse_pos = repell(mouse_pos, target_pos, thresh=120, force=0.03) # TODO: make parameter
                mouse.setPos((new_mouse_pos[0],new_mouse_pos[1]+1)) # +1 because of bug with setPos()
            if (dist_type == "burst"):
                if timer.getTime() >= burst_time and timer.getTime() <= burst_time+burst_dur:
                    new_mouse_pos = [mouse_pos[0]+burst_force,mouse_pos[1]]
                    mouse.setPos((new_mouse_pos[0],new_mouse_pos[1]+1)) # +1 because of bug with setPos()
                else: 
                    new_mouse_pos = mouse_pos

            # Draw Stuff
            target_circle.draw()
            new_circle(win,new_mouse_pos).draw()
            win.flip()

            # Breakout condition
            dist = math.dist(new_mouse_pos, target_pos)
            if dist < hit_radius:
                completed = True
            core.wait(0.005)

        # Move mouse back
        back = False
        mouse.setPos(target_pos)
        while not back:
            new_circle(win,mouse.getPos()).draw() 
            new_circle(win,spawn, color=(200,200,255)).draw() # TODO: Use cross instead
            win.flip()

            if math.dist(mouse.getPos(), spawn) < hit_radius:
                back = True
            core.wait(0.005)

        # Ask question
        feedback_text = visual.TextStim(
                win,
                units="norm",
                text=("Press Y if you felt a distortion in your arm and N if you did not. \nPress Q to quit"),
                wrapWidth=0.9,
                height=0.05
        )
        feedback_text.draw()
        win.flip()

        pressed_key = event.waitKeys(keyList=["q","y","n"])
        if pressed_key[0][0] == "q":
            win.setMouseVisible(True)
            win.close()
            core.quit()
        core.wait(0.2)
    # END SESSION
    win.setMouseVisible(True)
    win.close()
    core.quit()

def new_circle(win, pos: tuple, r=10,color=(255,255,255)):
    new_circ=visual.Circle(
            win,
            radius = r,
            pos = pos,
            opacity = 1,
            fillColor = color,
            colorSpace = 'rgb255')
    return new_circ

def rotate_point(point, deg, origin=(0,0)):
    angle = np.deg2rad(deg)
    x = point[0]-origin[0]
    y = point[1]-origin[1]
    newx = math.cos(angle)*x - math.sin(angle)*y
    newy = math.sin(angle)*x + math.cos(angle)*y
    return (newx+origin[0],newy+origin[1])

def repell(point, target, thresh, force):
    dist = math.dist(point, target)
    newx = point[0]+np.sign(point[0]-target[0])*math.ceil(force*max(0,thresh-dist))
    newy = point[1]+np.sign(point[1]-target[1])*math.ceil(force*max(0,thresh-dist))
    return (newx,newy)

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

@click.option(
        "-d",
        "--distortion",
        default="random",
        type=str,
        show_default=True,
        help="set distortion to one of [random,none,straight,rotate,repell,burst].",
)

def cli(screen: int, debug: bool, distortion: str):
    main(
        screen=screen,
        debug=debug,
        distortion=distortion,
    )


if __name__ == "__main__":
    cli()
