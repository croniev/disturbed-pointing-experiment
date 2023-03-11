from pathlib import Path
import os
from PIL.Image import blend
import numpy as np
import pandas as pd
import random
from datetime import datetime
import sys
import click
import warnings
from psychopy import prefs, monitors
from psychopy.visual.window import Window
from psychopy.event import Mouse
from psychopy import core
from psychopy.tools import monitorunittools
import math
from psychopy import core, event, visual
import bisect

# to avoid bug on windows (https://www.psychopy.org/troubleshooting.html#errors-with-getting-setting-the-gamma-ramp)
prefs.general["gammaErrorPolicy"] = "warn"
size = 250

warnings.simplefilter(action='ignore', category=FutureWarning)

# PARAMETERS
touch_radius = 25 # How close one has to be to beginning or orientation point
n_training = 1 # How many training blocks are performed
n_trials = 3 # How many normal blocks are performed
block_size = 30 # How many trials are in on block
orientation_point = [0,-350] # Position of point that has to be cut
beginning_point = [0,-470] # Position of point that needs to be gone back to
target_pos = (0,300) # not used
top_pos  =(0,350) # Where mouse will spawn after task and reference point for scoring
time_score_dist_crit = 60 # How far the mouse has to have been away from top to be penalized
time_score_time_crit = 7 # How many steps too fast mouse has to have been to be penalized
refresh_rate=0.0001 # After how much time mouse position is updated
disturb_prob = 0.2 # How likely a disturbtion is to occur in a normal trial
burst_time = 0.17 # After how much time the burst disturbtion starts
burst_dur = 0.2 # How long the burst disturbtion is applied
burst_force = -20 # Horizontal force of the burst disturbtion
time_limit = 0.4 # How much time one has for a trial
question_prob = 0.4 # Likelihood of subjective reporting in a non-disturbtion trial

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

    # START EXPERIMENT
    mouse = Mouse(visible=False, win = win)
    start_experiment(win, mouse)
    core.wait(0.3)
    score = None
    timing = None

    # DATA COLLECTION
    columns = ['trial_nr','is_training','block_size','block_nr'] # TODO: What data should be saved
    df = pd.DataFrame(columns=columns) 
    df["is_training"]=df["is_training"].astype(bool)
    trial_nr = 0
    block_nr = 1
    
    training = True
    while (True):
        # Pause
        if trial_nr % block_size == 0 and trial_nr != 0:
            block_nr += 1
            if (block_nr > n_training+n_trials):
                break

            if (block_nr >= n_training and training):
                training = False
                visual.TextStim(win,
                        units="norm",
                        text=("You have completed the training block.\nPress 'space' to start with the experiment."),
                        wrapWidth=0.9,
                        height=0.05
                ).draw()
            else:
                visual.TextStim(win,
                        units="norm",
                        text=("You have completed a block.\nRelax for a bit.\nPress 'space' when you are ready to continue."),
                        wrapWidth=0.9,
                        height=0.05
                ).draw()

            win.flip()
            if event.waitKeys(keyList=["space","q"])[0] == "q":
                win.setMouseVisible(True)
                win.close()
                core.quit()

        trial_nr += 1
        trial_data = {"trial_nr":[trial_nr],"is_training":[training],"block_size":[block_size],"block_nr":[block_nr]}
        back = False
        if len(event.getKeys(keyList=['q'])) > 0:
            win.setMouseVisible(True)
            win.close()
            core.quit()

        # Preparation - move mouse back
        started = False
        mouse.setPos(top_pos)
        while not back:
            if len(event.getKeys(keyList=['q'])) > 0: # DEBUG
                win.setMouseVisible(True)
                win.close()
                core.quit()

            # Show score
            visual.TextStim(win,
                    units="norm",
                    text=(str(timing)+"\nScore: "+str(score)),
                    wrapWidth=0.9,
                    height=0.035,
                    alignText="left"
            ).draw()

            if training:
                visual.Line(win,
                        start=(0,-1000),
                        end=(0,1000),
                        lineWidth=5,
                        color=(0,0,0),
                        colorSpace='rgb255'
                        ).draw()
            
            if not(started):
                new_circle(win, beginning_point, r=touch_radius, color=(200,200,255)).draw()
                new_circle(win,mouse.getPos(), color=(0,200,5)).draw() 
                if math.dist(mouse.getPos(),beginning_point) < touch_radius:
                    started = True
            else:
                new_circle(win,orientation_point, r=7, color=(200,200,255)).draw() 
                new_circle(win,mouse.getPos()).draw() 
                if math.dist(mouse.getPos(), orientation_point) < touch_radius:
                    back = True
            win.flip()
            core.wait(refresh_rate)

        # Pick distortion
#        if distortion == "random":
#            dist_type = np.random.choice(["none","straight","rotate","repell","burst"],p=[0.8,0.05,0.05,0.05,0.05])
#        else:
#            dist_type = distortion
        if (training):
            dist_type = "none"
        else:
            dist_type = np.random.choice(["none","burst"],p=[1-disturb_prob,disturb_prob])

        timer = core.Clock()
        offset = 0

        # Task
        completed = False
        y_array = []
        err=0
        while(not completed):
            if len(event.getKeys(keyList=['q'])) > 0: # DEBUG
                win.setMouseVisible(True)
                win.close()
                core.quit()
            mouse_pos = mouse.getPos()

#            # Distortions
#            if (dist_type == "none"):
#                virtual_mouse_pos = (mouse_pos[0],mouse_pos[1])
#            if (dist_type == "straight"):
#                virtual_mouse_pos = (0,mouse_pos[1])
#            if (dist_type == "rotate"):
#                virtual_mouse_pos = rotate_point(mouse_pos, 30, origin=(0,-200)) 
#            if (dist_type == "repell"):
#                virtual_mouse_pos = repell(mouse_pos, target_pos, thresh=120, force=0.03) 
#                mouse.setPos((virtual_mouse_pos[0],virtual_mouse_pos[1]+1)) # +1 because of bug with setPos()
#            if (dist_type == "burst"):
#                if timer.getTime() >= burst_time and timer.getTime() <= burst_time+burst_dur:
#                    virtual_mouse_pos = [mouse_pos[0]+burst_force,mouse_pos[1]]
#                    mouse.setPos((virtual_mouse_pos[0],virtual_mouse_pos[1]+1)) # +1 because of bug with setPos()
#                else: 
#                    virtual_mouse_pos = mouse_pos

            # Apply Distortion
            if (dist_type == "burst" and timer.getTime() >= burst_time and timer.getTime() <= burst_time+burst_dur):
                offset += burst_force
            virtual_mouse_pos = [mouse_pos[0]+offset,mouse_pos[1]]

            # Draw Stuff
            if training:
                visual.Line(win,
                        start=(0,-1000),
                        end=(0,1000),
                        lineWidth=5,
                        color=(0,0,0),
                        colorSpace='rgb255'
                        ).draw()
            new_circle(win,orientation_point, r=7, color=(100,255,100)).draw() 
            new_circle(win,virtual_mouse_pos).draw()
            win.flip()

            # Scoring
            y_array.append(mouse_pos[1])
            err += np.absolute(0-mouse_pos[0]) # TODO: use mouse pos or virtual mouse pos?

            # Breakout condition
            if timer.getTime() >= time_limit:
                completed = True
            core.wait(refresh_rate)

        score, timing = scoring(y_array, err)
        # Ask question
        if not(training) and (dist_type=="burst" or np.random.choice([True,False],p=[question_prob,1-question_prob])):
            feedback_text = visual.TextStim(
                    win,
                    units="norm",
                    text=("Press Y if you felt a distortion in your arm and N if you did not."),
                    wrapWidth=0.9,
                    height=0.05
            )
            feedback_text.draw()
            win.flip()
            pressed_key = event.waitKeys(keyList=["q","y","n"])
            if pressed_key[0][0] == "q": # DEBUG
                win.setMouseVisible(True)
                win.close()
                core.quit()
        else:
            win.flip()
            core.wait(0.2)

        # Add data to df
        tmp = pd.DataFrame.from_dict(trial_data)
        df = pd.concat([df,tmp],ignore_index=True)

    # END SESSION
    feedback_text = visual.TextStim(
            win,
            units="norm",
            text=("You have completed the experiment!\nThank you very much for your participation, have a nice day."),
            wrapWidth=0.9,
            height=0.05
    ).draw()
    win.flip()
    event.waitKeys()
    win.setMouseVisible(True)
    win.close()
    df.to_csv('data.csv', index=False) # TODO: different file names for participants
    core.quit()

def start_experiment(win,mouse):
    instruction_text = visual.TextStim(
        win,
        units="norm",
        text=(
            "Your task is to move your cursor up in a straight line. First you will complete some training trials, and then the experiment will beginn.\nWhen the cursor is green, please move it back to the orientation_point point. It will then turn white, and you should again move it in a straight line.\n\nDuring the experiment, press 'q' to quit. \nPress space to continue."
        ),
        wrapWidth=0.9,
        height=0.05,
    )
    instruction_text.draw()
    win.setMouseVisible(False)
    win.flip()
    pressed_key = event.waitKeys(keyList=["space","q"])
    if pressed_key[0][0] == "q": #DEBUG
        win.setMouseVisible(True)
        win.close()
        core.quit()
    mouse.clickReset()
    win.flip()

def new_circle(win, pos: tuple, r=10,color=(255,255,255)):
    new_circ=visual.Circle(
            win,
            radius = r,
            pos = pos,
            opacity = 1,
            fillColor = color,
            colorSpace = 'rgb255')
    return new_circ

def scoring(y_array, err):
    score = 1000

    # score for time
    timing = "Good Timing"
    reach_top_idx = bisect.bisect_left(y_array, top_pos[1])
    print(y_array)
    print(reach_top_idx)
    if reach_top_idx == len(y_array): # i.e. top was not reached
        min_dist = np.absolute(top_pos[1]-max(y_array))
        if(min_dist > time_score_dist_crit):
            timing = "Too slow (too short)!"
            score -= min_dist # TODO: how this?
    elif reach_top_idx <= time_score_time_crit:
        timing = "Too fast!"
        score -= (reach_top_idx)/10 # TODO: how this?

    # score for straight
    score -= err # TODO: how this?
    return int(np.round(score)), timing

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
