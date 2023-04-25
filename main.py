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
from itertools import product
import math
from psychopy import core, event, visual
import bisect
import json

# to avoid bug on windows (https://www.psychopy.org/troubleshooting.html#errors-with-getting-setting-the-gamma-ramp)
prefs.general["gammaErrorPolicy"] = "warn"
size = 250

warnings.simplefilter(action='ignore', category=FutureWarning)

# TODO: Store parameters in and load from json
with open('params.json') as json_data:
    PARAMS = json.load(json_data)
# PARAMETERS
touch_radius = 25  # How close one has to be to beginning or orientation point
n_proprioceptive_reporting = 2  # How many trials the baseline proprioceptive reporting should consist of
n_training = 0  # How many training blocks are performed
block_size = 4  # How many trials are in on block
orientation_point = [0, -350]  # Position of point that has to be cut
beginning_point = [0, -470]  # Position of point that needs to be gone back to
target_pos = (0, 300)  # not used
top_pos = (0, 350)  # Where mouse will spawn after task and reference point for scoring
prop_report_beginnings = [beginning_point, top_pos, [0, 0]]  # Points to move to before proprioceptive reporting
time_score_dist_crit = 60  # How far the mouse has to have been away from top to be penalized
time_score_time_crit = 7  # How many steps too fast mouse has to have been to be penalized
refresh_rate = 0.0001  # After how much time mouse position is updated
disturb_prob = 1  # 0.2  # How likely a disturbtion is to occur in a normal trial
burst_time = [0.10, 0.13, 0.16]  # After how much time the burst disturbtion starts
burst_dur = [0.1, 0.2, 0.3]  # How long the burst disturbtion is applied
burst_force = [-10, 10, -20, 20, -30, 30]  # Horizontal force of the burst disturbtion
burst_combis = list(product(burst_time, burst_dur, burst_force))
n_trials = len(burst_combis)  # How many normal blocks are performed
show_score_every_n_trials = 6  # After how many trials the score is shown (always shown in training)
time_limit = 0.4  # How much time one has for a trial
question_prob = 0.4  # Likelihood of subjective reporting in a non-disturbtion trial
p_x, p_y = 200, 200
proprio_targets = [[-p_x, p_y], [p_x, p_y], [p_x, -p_y], [-p_x, -p_y]]  # Possible targets for proprioceptive reporting


def main(
    screen: int = 0,
    debug: bool = False,
    distortion: str = "random",
    no_propriocept: bool = False,
    user: int = 0,
    lefthanded: bool = False,
) -> None:
    # Open a PsychoPy window, show the image, collect a keypress, close.
    win = visual.Window(
        # (500, 500),  # arbitrary if we're doing fullscreen
        screen=screen,
        units="pix",
        allowGUI=True,
        fullscr=not (debug),  # FINAL: debug auf False setzen
    )

    # Save Params and Flags in own file
    PARAMS.update({"debug": debug, "distortion": distortion, "no_propriocept": no_propriocept, "lefthanded": lefthanded})
    pd.DataFrame.from_dict(PARAMS).to_csv(str("data/" + user + "_params.csv"), index=False)

    # SHAPES
    training_line = visual.Line(win,
                                start=(0, -1000),
                                end=(0, 1000),
                                lineWidth=5,
                                color=(0, 0, 0),
                                colorSpace='rgb255')
    beginning_point_shape = new_circle(win, beginning_point, r=touch_radius, color=(200, 200, 255))
    orientation_point_shape = new_circle(win, orientation_point, r=7, color=(200, 200, 255))

    # TEXTS
    text_stim_block_complete = visual.TextStim(win,
                                               units="norm",
                                               text=("You have completed a block.\nRelax for a bit.\nPress 'space' when you are ready to continue."),
                                               wrapWidth=0.9,
                                               height=0.05)
    text_stim_trianing_complete = visual.TextStim(win,
                                                  units="norm",
                                                  text=("You have completed the training block.\nPress 'space' to start with the experiment."),
                                                  wrapWidth=0.9,
                                                  height=0.05)
    text_stim_score = visual.TextStim(win,
                                      units="norm",
                                      wrapWidth=0.9,
                                      height=0.035,
                                      alignText="left")
    text_stim_feedback = visual.TextStim(win,
                                         units="norm",
                                         text=("Press <A> or <left arrow> if you felt a distortion in your arm and <S> or <right arrow> if you did not."),
                                         wrapWidth=0.9,
                                         height=0.05)
    text_stim_end = visual.TextStim(win,
                                    units="norm",
                                    text=("You have completed the experiment!\nThank you very much for your participation, have a nice day."),
                                    wrapWidth=0.9,
                                    height=0.05)

    # START EXPERIMENT
    mouse = Mouse(visible=True, win=win)  # Change visibility to False
    if not (no_propriocept):
        # Baseline proprioceptive reporting beginning
        proprioceptive_reporting(n_proprioceptive_reporting, str(user + "_beginning.csv"), True, win, mouse)
    start_experiment(win, mouse)
    core.wait(0.3)
    score = None
    timing = None

    # DATA COLLECTION
    columns = ['trial_nr', 'training', 'block_nr', 'dist_type', 'burst_dur', 'burst_time', 'burst_force', 'back_movement', 'back_timestamps', 'starting_movement', 'starting_timestamps', 'mouse_poss', 'virtual_poss', 'poss_timestamps', 'score', 'question_asked', 'answer', 'pr_mouse_beginn', 'pr_mouse_pos', 'pr_target', 'pr_hit', 'pr_trajectory']
    df = pd.DataFrame(columns=columns)
    df["is_training"] = df["is_training"].astype(bool)

    trial_nr = 0
    block_nr = 1
    if (n_training > 0):
        training = True
    else:
        training = False

    # Main loop
    while (True):
        # Check for blocks
        if trial_nr % block_size == 0 and trial_nr != 0:
            block_nr += 1
            if (block_nr > n_training + n_trials):
                break

            if (block_nr >= n_training and training):
                training = False
                text_stim_trianing_complete.draw()
            else:
                text_stim_block_complete.draw()

            win.flip()
            if event.waitKeys(keyList=["space", "q"])[0] == "q":
                win.setMouseVisible(True)
                win.close()
                core.quit()

        trial_nr += 1
        trial_data = {"trial_nr": [trial_nr], "training": [training], "block_nr": [block_nr]}
        back = False
        if len(event.getKeys(keyList=['q'])) > 0:
            win.setMouseVisible(True)
            win.close()
            core.quit()

        # PHASE 1: Preparation - move mouse back
        burst_time, burst_dur, burst_force = burst_combis[block_nr - n_training - 1]
        back_home = False
        # mouse.setPos(top_pos)  # should this be changed?
        if (trial_nr % show_score_every_n_trials == 0 or training):
            text_stim_score.text = (str(timing) + "\nScore: " + str(score)) + "\nTime:" + str(burst_time) + "\nDur:" + str(burst_dur) + "\nForce:" + str(burst_force)
        else:
            text_stim_score.text = "\nTime:" + str(burst_time) + "\nDur:" + str(burst_dur) + "\nForce:" + str(burst_force)

        # Move mouse back
        timer = core.Clock()
        back_movement = []
        starting_movement = []
        back_timestamps = []
        starting_timestamps = []
        while not back:
            if len(event.getKeys(keyList=['q'])) > 0:  # DEBUG
                win.setMouseVisible(True)
                win.close()
                core.quit()

            text_stim_score.draw()

            if training:
                training_line.draw()

            mouse_pos = mouse.getPos()
            if not (back_home):
                beginning_point_shape.draw()
                new_circle(win, mouse_pos, color=(0, 200, 5)).draw()
                back_movement.append(mouse_pos)
                back_timestamps.append(timer.getTime())
                if math.dist(mouse_pos, beginning_point) < touch_radius:
                    back_home = True
                    timer = core.Clock()
            else:  # PHASE 2: Move upwards
                orientation_point_shape.draw()
                new_circle(win, mouse_pos).draw()
                starting_movement.append(mouse_pos)
                starting_timestamps.append(timer.getTime())
                if math.dist(mouse_pos, orientation_point) < touch_radius:
                    back = True
            win.flip()
            core.wait(refresh_rate)
        trial_data.update({"back_movement": back_movement, "back_timestamps": back_timestamps, "starting_movement": starting_movement, "starting_timestamps": starting_timestamps})

        # Pick distortion
#        if distortion == "random":
#            dist_type = np.random.choice(["none","straight","rotate","repell","burst"],p=[0.8,0.05,0.05,0.05,0.05])
#        else:
#            dist_type = distortion
        if (training):
            dist_type = "none"
        else:
            dist_type = np.random.choice(["none", "burst"], p=[1 - disturb_prob, disturb_prob])

        trial_data.update({"dist_type": dist_type, "burst_dur": burst_dur, "burst_time": burst_time, "burst_force": burst_force})
        timer = core.Clock()
        offset = 0

        # PHASE 2: Pointing Task
        completed = False
        mouse_poss = []
        virtual_poss = []
        poss_timestamps = []
        err = 0
        while (not completed):
            if len(event.getKeys(keyList=['q'])) > 0:  # DEBUG
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
            # Es sieht anders aus als es ist ==> wir behalten die Information darüber, wo die Hand actually ist.
            if (dist_type == "burst" and timer.getTime() >= burst_time and timer.getTime() <= burst_time + burst_dur):
                offset += burst_force
            virtual_mouse_pos = [mouse_pos[0] + offset, mouse_pos[1]]

            # Save movements with times
            mouse_poss.append(mouse_pos)
            virtual_poss.append(virtual_mouse_pos)
            poss_timestamps.append(timer.getTime())

            # Draw Stuff
            if training:
                training_line.draw()
            orientation_point_shape.draw()
            new_circle(win, virtual_mouse_pos).draw()
            win.flip()

            # Scoring
            err += np.absolute(0 - virtual_mouse_pos[0])
            # Breakout condition
            if timer.getTime() >= time_limit:
                completed = True
            core.wait(refresh_rate)

        score, timing = scoring(list(np.array(virtual_mouse_pos)[:, 1]), err)
        trial_data.update({'mouse_poss': mouse_poss, 'virtual_poss': virtual_poss, 'poss_timestamps': poss_timestamps, 'score': score})
        # PHASE 3: Ask question
        if not (training) and (dist_type == "burst" or np.random.choice([True, False], p=[question_prob, 1 - question_prob])):
            text_stim_feedback.draw()
            win.flip()
            pressed_key = event.waitKeys(keyList=["q", "a", "s", "left", "right"])
            if pressed_key[0][0] == "q":  # DEBUG
                win.setMouseVisible(True)
                win.close()
                core.quit()
            elif pressed_key[0][0] == "a" or pressed_key[0][0] == "left":
                trial_data.update({"question_asked": True, "subj_answer": True})
            elif pressed_key[0][0] == "s" or pressed_key[0][0] == "right":
                trial_data.update({"question_asked": True, "subj_answer": False})
        else:
            trial_data.update({"question_asked": False})  # If no question is asked
            win.flip()
            core.wait(0.2)

        # PHASE 4: Proprioception reporting guess
        # TODO: Only makes sense when trackpad is absolute, not relative
        if (not (no_propriocept)):
            pr_data = proprioceptive_reporting(1, "", training, win, mouse)
            trial_data.update(pr_data)

        # Add data to df
        df = pd.concat([df, pd.DataFrame.from_dict(trial_data)], ignore_index=True)

    if not (no_propriocept):
        # Proprioceptive baseline at end
        proprioceptive_reporting(n_proprioceptive_reporting, str(user + "_ending.csv"), True, win, mouse)

    # END SESSION
    text_stim_end.draw()
    win.flip()
    event.waitKeys()
    win.setMouseVisible(True)
    win.close()
    df.to_csv(str("data/" + user + "_data.csv"), index=False)
    core.quit()


def proprioceptive_reporting(n, filename, show_feedback, win, mouse):
    # TODO: Add a text stim!
    prop_data = pd.DataFrame(columns=["pr_mouse_beginn", "pr_mouse_pos", "pr_target", "pr_hit", "pr_trajectory"])
    for i in range(n):
        single_data = {}
        if (filename != ""):
            # Move mouse to certain point
            beginning_point = prop_report_beginnings[np.random.choice(len(prop_report_beginnings))]
            beginning_point_shape = new_circle(win, beginning_point, r=touch_radius, color=(200, 200, 255))
            ready = False
            while (not ready):
                if len(event.getKeys(keyList=['q'])) > 0:  # DEBUG
                    win.setMouseVisible(True)
                    win.close()
                    core.quit()

                beginning_point_shape.draw()
                new_circle(win, mouse.getPos(), color=(0, 200, 5)).draw()
                if math.dist(mouse.getPos(), beginning_point) < touch_radius:
                    ready = True
                win.flip()
                core.wait(refresh_rate)

        target = proprio_targets[np.random.randint(len(proprio_targets))]
        target_shape = new_circle(win, target, r=touch_radius)
        target_shape.draw()
        win.flip()
        hit = False
        single_data = {"pr_mouse_beginn": mouse.getPos()}
        trajectory = []
        while True:
            trjectory.append(mouse.getPos())
            if mouse.isPressedIn(target_shape):
                hit = True
                break
            elif np.sum(mouse.getPressed()) != 0:
                break
        single_data.update({"pr_mouse_pos": [mouse.getPos()], "pr_target": [target], "pr_hit": [hit], "pr_trajectory": pr_trajectory})
        if show_feedback:
            if hit:
                new_circle(win, target, r=touch_radius, color=(0, 240, 0)).draw()
            else:
                new_circle(win, target, r=touch_radius, color=(240, 0, 0)).draw()
            new_circle(win, mouse.getPos()).draw()
            win.flip()
            core.wait(0.6)

        if (filename == ""):
            return single_data
        prop_data = pd.concat([prop_data, pd.DataFrame.from_dict(single_data)], ignore_index=True)

    prop_data.to_csv(str("data/" + filename), index=True)


def start_experiment(win, mouse):
    instruction_text = visual.TextStim(
        win,
        units="norm",
        text=(
            "Your task is to move your cursor up in a straight line. First you will complete some training trials, and then the main task will beginn.\nWhen the cursor is green, please move it back to the beginning point. It will then turn white, and you should again move it in a straight line.\n\nDuring the experiment, press 'q' to quit. \nPress space to continue."
        ),
        wrapWidth=0.9,
        height=0.05,
    )
    instruction_text.draw()
    win.flip()
    pressed_key = event.waitKeys(keyList=["space", "q"])
    if pressed_key[0][0] == "q":  # DEBUG
        win.setMouseVisible(True)
        win.close()
        core.quit()
    mouse.clickReset()
    win.flip()


def new_circle(win, pos: tuple, r=10, color=(255, 255, 255)):
    new_circ = visual.Circle(win,
                             radius=r,
                             pos=pos,
                             opacity=1,
                             fillColor=color,
                             colorSpace='rgb255')
    return new_circ


def scoring(y_array, err):
    score = 1000

    # score for time
    timing = "Good Timing"
    reach_top_idx = bisect.bisect_left(y_array, top_pos[1])
    if reach_top_idx == len(y_array):  # i.e. top was not reached
        min_dist = np.absolute(top_pos[1] - max(y_array))
        if (min_dist > time_score_dist_crit):
            timing = "Too slow (too short)!"
            score -= min_dist
    elif reach_top_idx <= time_score_time_crit:  # i.e. top was reached too soon
        timing = "Too fast!"
        score -= (reach_top_idx) / 10

    # score for straight
    score -= err
    return int(np.round(score)), timing


def rotate_point(point, deg, origin=(0, 0)):
    angle = np.deg2rad(deg)
    x = point[0] - origin[0]
    y = point[1] - origin[1]
    newx = math.cos(angle) * x - math.sin(angle) * y
    newy = math.sin(angle) * x + math.cos(angle) * y
    return (newx + origin[0], newy + origin[1])


def repell(point, target, thresh, force):
    dist = math.dist(point, target)
    newx = point[0] + np.sign(point[0] - target[0]) * math.ceil(force * max(0, thresh - dist))
    newy = point[1] + np.sign(point[1] - target[1]) * math.ceil(force * max(0, thresh - dist))
    return (newx, newy)


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
@click.option(
    "-n",
    "--no-propriocept",
    default=False,
    show_default=True,
    is_flag=True,
    help="Pass to disable proprioceptive reporting after moving.",
)
@click.option(
    "-u",
    "--user",
    default=0,
    type=int,
    show_default=True,
    help="ID of the participant",
)
@click.option(
    "-l",
    "--lefthanded",
    default=False,
    show_default=True,
    is_flag=True,
    help="Pass to save lefthanded flag in data",
}
def cli(screen: int, debug: bool, distortion: str, no_propriocept: bool, user: int):
    main(
        screen=screen,
        debug=debug,
        distortion=distortion,
        no_propriocept=no_propriocept,
        user=user,
        lefthanded=lefthanded
    )


if __name__ == "__main__":
    cli()
