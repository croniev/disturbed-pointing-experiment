import os
import threading
import platform, sys
import numpy as np
import pandas as pd
import click
import warnings
from psychopy import prefs, monitors, core, event, visual
from psychopy.event import Mouse
from itertools import product
from random import shuffle
import math
import bisect
import json
import bioplux as bp

# to avoid bug on windows (https://www.psychopy.org/troubleshooting.html#errors-with-getting-setting-the-gamma-ramp)
prefs.general["gammaErrorPolicy"] = "warn"
size = 250

warnings.simplefilter(action='ignore', category=FutureWarning)

sys.path.append(f"PLUX-API-Python3/Win{platform.architecture()[0][:2]}_{''.join(platform.python_version().split('.')[:2])}") # not sure for what. from bioPLUX example

# Parameters
with open('params.json') as json_data:
    PARAMS = json.load(json_data)
touch_radius, n_proprioceptive_reporting, block_size, orientation_point, beginning_point, target_pos, top_pos, time_score_dist_crit, time_score_time_crit, refresh_rate, disturb_prob, burst_time, burst_dur, burst_force, show_score_every_n_trials, time_limit, question_prob, p_x, p_y, burst_t_f_ds, address = [PARAMS.get(k)[0] for k in ["touch_radius", "n_proprioceptive_reporting", "block_size", "orientation_point", "beginning_point", "target_pos", "top_pos", "time_score_dist_crit", "time_score_time_crit", "refresh_rate", "disturb_prob", "burst_time", "burst_dur", "burst_force", "show_score_every_n_trials", "time_limit", "question_prob", "p_x", "p_y", "burst_t_f_ds", "address"]]
burst_combis = list(product(burst_time, burst_force))
trial_list = [k for k in burst_combis for i in range(15)] + [[0, 0] for i in range(int(np.round(15 * len(burst_combis) * (1 - disturb_prob) / disturb_prob)))]
n_trials = np.round(len(trial_list) / block_size)  # How many normal blocks are performed?
shuffle(trial_list)


def norm2pix(pos, mon):
    mon_size = mon.getSizePix()
    return [round(pos[0] * mon_size[0] / 2), round(pos[1] * mon_size[1] / 2)]


# Normalizing with the screen specs.
mon = monitors.Monitor("monitor_disturbed_pointing")
p_x, p_y = norm2pix([p_x, p_y], mon)
proprio_targets = [[-p_x, p_y], [p_x, p_y], [p_x, -p_y], [-p_x, -p_y]]  # Possible targets for proprioceptive reporting

orientation_point = norm2pix(orientation_point, mon)
beginning_point = norm2pix(beginning_point, mon)
target_pos = norm2pix(target_pos, mon)
top_pos = norm2pix(top_pos, mon)


def main(
    screen: int = 0,
    debug: bool = False,
    distortion: str = "random",
    no_propriocept: bool = False,
    no_training: bool = False,
    user: str = "0",
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

    # Save flags in PARAMS dict
    PARAMS.update({"debug": debug, "distortion": distortion, "no_propriocept": no_propriocept, "lefthanded": lefthanded})

    # create shapes and texts
    training_line, beginning_point_shape, op_line_x, op_line_y, text_stim_prop_reporting, text_stim_prop_reporting_2, text_stim_block_complete_saving, text_stim_score, text_stim_feedback, text_stim_feedback_lh, text_stim_end, text_stim_entering_phase2, text_stim_begin = stims(win)

    # DATA COLLECTION
    os.makedirs("./data", exist_ok=True)
    if os.path.isfile(str("data/" + user + "_data.csv")):
        os.remove(str("data/" + user + "_data.csv"))
    if os.path.isfile(str("data/" + user + "_beginning.csv")):
        os.remove(str("data/" + user + "_beginning.csv"))
    if os.path.isfile(str("data/" + user + "_ending.csv")):
        os.remove(str("data/" + user + "_ending.csv"))
    if os.path.isfile("tmp"):
        os.remove("tmp")
    df = pd.DataFrame()

    # START EXPERIMENT
    mouse = Mouse(visible=False, win=win)

    start_experiment(win, mouse)
    core.wait(0.3)
    score = None
    timing = None

    trial_nr = 0
    block_nr = 0
    phase2 = False
    if (not no_training):
        training = True
    else:
        training = False
        phase2 = True

    while (True):  # Main loop
        if trial_nr % block_size == 0 and trial_nr != 0:  # Check for blocks

            if (training):
                text_stim_block_complete_saving.text = "You have completed a training block.\n\nSaving data... please wait"
            else:
                text_stim_block_complete_saving.text = "You have completed a block.\nRelax for a bit.\n\nSaving data... please wait"
                block_nr += 1
            text_stim_block_complete_saving.draw()
            win.flip()

            try:
                tmp = pd.read_csv(str("data/" + user + "_data.csv"))
                tmp = pd.concat([tmp, df], ignore_index=True)
            except FileNotFoundError:
                tmp = df
            tmp.to_csv(str("data/" + user + "_data.csv"), index=False)
            df = pd.DataFrame()

            if (training and not phase2):
                if not lefthanded:
                    text_stim_block_complete_saving.text = text_stim_block_complete_saving.text.replace("Saving data... please wait", "Press <space> to perform another block or <a> to continue to training phase two.")
                else:
                    text_stim_block_complete_saving.text = text_stim_block_complete_saving.text.replace("Saving data... please wait", "Press <space> to perform another block or <left> to continue to training phase two.")
            elif (training and phase2):
                if not lefthanded:
                    text_stim_block_complete_saving.text = text_stim_block_complete_saving.text.replace("Saving data... please wait", "Press <space> to perform another block or <a> to continue to the main experiment.")
                else:
                    text_stim_block_complete_saving.text = text_stim_block_complete_saving.text.replace("Saving data... please wait", "Press <space> to perform another block or <left> to continue to the main experiment.")
            else:
                text_stim_block_complete_saving.text = text_stim_block_complete_saving.text.replace("Saving data... please wait", "Press <space> to continue.")
            text_stim_block_complete_saving.draw()
            win.flip()

            pressed_key = event.waitKeys(keyList=["space", "a", "left", "q"])[0]
            if pressed_key == "q":
                win.setMouseVisible(True)
                win.close()
                core.quit()
            elif (pressed_key == "a" or pressed_key == "left") and not phase2:
                phase2 = True
                text_stim_entering_phase2.draw()
                win.flip()
                event.waitKeys(keyList=["space"])
            elif ((pressed_key == "a" or pressed_key == "left") and phase2):
                training = False
                trial_nr = 0
                # Baseline proprioceptive reporting beginning
                if not (no_propriocept):
                    text_stim_prop_reporting.draw()
                    win.flip()
                    event.waitKeys(keyList=["space"])
                    proprioceptive_reporting(n_proprioceptive_reporting, str(user + "_beginning.csv"), False, win, mouse)
                    text_stim_begin.draw()
                    win.flip()
                    event.waitKeys(keyList=["space"])
            if (block_nr >= n_trials):
                break

        if (trial_nr == 0 and no_training) and not no_propriocept:
            text_stim_prop_reporting.draw()
            win.flip()
            event.waitKeys(keyList=["space"])
            proprioceptive_reporting(n_proprioceptive_reporting, str(user + "_beginning.csv"), False, win, mouse)
            text_stim_begin.draw()
            win.flip()
            event.waitKeys(keyList=["space"])

        trial_nr += 1
        trial_data = {"trial_nr": [trial_nr], "training": [training], "block_nr": [block_nr]}
        trial_data.update(PARAMS)
        if len(event.getKeys(keyList=['q'])) > 0:
            win.setMouseVisible(True)
            win.close()
            core.quit()

        # PHASE 1: Preparation - move mouse back
        try:
            trial_burst_time, trial_burst_force = trial_list[trial_nr - 1]  # burst_combis[block_nr]
        except IndexError:
            trial_burst_time, trial_burst_force = 0, 0
        # mouse.setPos(top_pos)  # should this be changed?
        if (trial_nr % show_score_every_n_trials == 0 or training):
            text_stim_score.text = (str(timing) + "\nScore: " + str(score)) #+ "\n\nTime:" + str(trial_burst_time) + "\nForce:" + str(trial_burst_force)
        else:
            text_stim_score.text = ""#"\n\nTime:" + str(trial_burst_time) + "\nForce:" + str(trial_burst_force)

        # EEG measurement
        eeg_data_back = []
        make_thread(eeg_data_back)  # BIO
        eeg_data_start = []

        # Move mouse back
        started = False
        back_home = False
        timer = core.Clock()
        back_movement = []
        starting_movement = []
        back_timestamps = []
        starting_timestamps = []
        while not started:
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
                # new_circle(win, mouse_pos, color=(0, 200, 5)).draw()
                back_movement.append(mouse_pos)
                back_timestamps.append(timer.getTime())
                if math.dist(mouse_pos, beginning_point) < touch_radius:
                    back_home = True
                    open("tmp", 'a').close()  # file presence terminates EEG thread
                    make_thread(eeg_data_start)  # BIO
                    timer = core.Clock()
            else:  # PHASE 2: Move upwards
                op_line_x.draw()
                op_line_y.draw()
                new_circle(win, mouse_pos).draw()
                starting_movement.append(mouse_pos)
                starting_timestamps.append(timer.getTime())
                if math.dist(mouse_pos, orientation_point) < 25:  # touch_radius:
                    started = True
                    open("tmp", 'a').close()  # file presence terminates EEG thread
            win.flip()
            core.wait(refresh_rate)
        trial_data.update({"back_movement": [back_movement], "back_timestamps": [back_timestamps], "starting_movement": [starting_movement], "starting_timestamps": [starting_timestamps]})
        trial_data.update({"eeg_data_start": eeg_data_start, "eeg_data_back": eeg_data_back})
        trial_data.update({"trial_burst_time": [trial_burst_time], "trial_burst_force": [trial_burst_force]})

        timer = core.Clock()
        offset = 0

        # EEG measurement
        eeg_data_trial = []
        make_thread(eeg_data_trial)  # BIO

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

            # Apply Distortion
            # Es sieht anders aus als es ist ==> wir behalten die Information darüber, wo die Hand actually ist.
            if (not training and timer.getTime() >= trial_burst_time and timer.getTime() <= trial_burst_time + burst_dur):
                offset += trial_burst_force
            virtual_mouse_pos = [mouse_pos[0] + offset, mouse_pos[1]]

            # Save movements with times
            mouse_poss.append(mouse_pos)
            virtual_poss.append(virtual_mouse_pos)
            poss_timestamps.append(timer.getTime())

            # Draw Stuff
            if training:
                training_line.draw()
            # op_line_x.draw()
            # op_line_y.draw()
            new_circle(win, virtual_mouse_pos).draw()
            win.flip()

            # Scoring
            err += np.absolute(0 - virtual_mouse_pos[0])
            # Breakout condition
            if timer.getTime() >= time_limit:
                completed = True
                open("tmp", 'a').close()  # file presence terminates EEG thread
            core.wait(refresh_rate)

        time_score, timing = time_scoring(list(np.array(virtual_poss)[:, 1]))
        # score for straight
        score = np.round(time_score - err)
        trial_data.update({'mouse_poss': [mouse_poss], 'virtual_poss': [virtual_poss], 'poss_timestamps': [poss_timestamps], 'score': [score], 'time_score': [time_score], 'err': [err], 'timing': [timing]})
        trial_data.update({"eeg_data_trial": eeg_data_trial})

        # PHASE 3: Proprioception reporting guess
        if (not (no_propriocept) and phase2):
            pr_data = proprioceptive_reporting(1, "", training, win, mouse)
            trial_data.update(pr_data)

        # PHASE 4: Ask question
        if phase2 and (trial_burst_force != 0 or np.random.choice([True, False], p=[question_prob, 1 - question_prob])):
            if not lefthanded:
                text_stim_feedback.draw()
            else:
                text_stim_feedback_lh.draw()
            win.flip()
            timer = core.Clock()
            pressed_key = event.waitKeys(keyList=["q", "a", "d", "left", "right"], timeStamped=timer)
            if pressed_key[0][0] == "q":  # DEBUG
                win.setMouseVisible(True)
                win.close()
                core.quit()
            elif pressed_key[0][0] == "a" or pressed_key[0][0] == "l":
                trial_data.update({"question_asked": [True], "subj_answer": [True], "answer_time": [pressed_key[0][1]]})
            elif pressed_key[0][0] == "d" or pressed_key[0][0] == "r":
                trial_data.update({"question_asked": [True], "subj_answer": [False], "answer_time": [pressed_key[0][1]]})
        else:
            trial_data.update({"question_asked": [False]})  # If no question is asked
            win.flip()
            core.wait(0.2)

        # Add data to df
        if (df.size < 1):
            df = pd.DataFrame.from_dict(trial_data)
        else:
            df = pd.concat([df, pd.DataFrame.from_dict(trial_data)], ignore_index=True)

    if not (no_propriocept):
        # Proprioceptive baseline at end
        text_stim_prop_reporting_2.draw()
        win.flip()
        event.waitKeys(keyList=["space"])
        proprioceptive_reporting(n_proprioceptive_reporting, str(user + "_ending.csv"), False, win, mouse)

    # END SESSION
    text_stim_end.draw()
    win.flip()
    event.waitKeys()
    win.setMouseVisible(True)
    win.close()
    core.quit()


def proprioceptive_reporting(n, filename, show_feedback, win, mouse):
    # prop_data = pd.DataFrame(columns=["pr_mouse_beginn", "pr_mouse_pos", "pr_target", "pr_hit", "pr_trajectory"])
    for i in range(n):
        single_data = {}
        if (filename != ""):
            # Move mouse to certain point
            beginning_point = [0, np.random.normal(loc=top_pos[1] + 50, scale=30)]
            bp_line_x = visual.Line(win,
                                    start=(beginning_point[0] - 10, beginning_point[1]),
                                    end=(beginning_point[0] + 10, beginning_point[1]),
                                    opacity=1,
                                    lineWidth=3,
                                    contrast=-1.0)
            bp_line_y = visual.Line(win,
                                    start=(beginning_point[0], beginning_point[1] - 10),
                                    end=(beginning_point[0], beginning_point[1] + 10),
                                    opacity=1,
                                    lineWidth=3,
                                    contrast=-1)
            ready = False
            while (not ready):
                if len(event.getKeys(keyList=['q'])) > 0:  # DEBUG
                    win.setMouseVisible(True)
                    win.close()
                    core.quit()

                bp_line_x.draw()
                bp_line_y.draw()
                new_circle(win, mouse.getPos(), color=(0, 200, 5)).draw()
                if math.dist(mouse.getPos(), beginning_point) < touch_radius:
                    ready = True
                win.flip()
                core.wait(refresh_rate)

        win.flip()
        core.wait(0.2)

        # EEG measurement
        eeg_data_pr = []
        make_thread(eeg_data_pr)  # BIO

        target = proprio_targets[np.random.randint(len(proprio_targets))]
        target_shape = new_circle(win, target, r=touch_radius)
        target_shape.draw()
        win.flip()
        hit = False
        single_data = {"pr_mouse_beginn": [mouse.getPos()]}
        trajectory = []
        timer = core.Clock()
        while True:
            trajectory.append(mouse.getPos())
            if mouse.getPressed()[1] != 0:
                if math.dist(mouse.getPos(), target) < touch_radius + 10:
                    hit = True
                open("tmp", 'a').close()  # file presence terminates EEG thread
                break
        single_data.update({"pr_mouse_pos": [mouse.getPos()], "pr_target": [target], "pr_distance": [math.dist(mouse.getPos(), target)], "pr_hit": [hit], "pr_trajectory": [trajectory], "pr_time": [timer.getTime()]})
        single_data.update({"eeg_data_pr": eeg_data_pr})

        if show_feedback:
            if hit:
                new_circle(win, target, r=touch_radius, color=(0, 240, 0)).draw()
            else:
                new_circle(win, target, r=touch_radius, color=(240, 0, 0)).draw()
            new_circle(win, mouse.getPos()).draw()
            win.flip()
        else:
            win.flip()
        core.wait(0.3)

        if (filename == ""):
            return single_data
        try:
            prop_data = pd.concat([prop_data, pd.DataFrame.from_dict(single_data)], ignore_index=True)
        except NameError:
            prop_data = pd.DataFrame.from_dict(single_data)

    visual.TextStim(win,
                    units="norm",
                    text=("Well Done!\n\nSaving data...\nPlease wait a moment"),
                    wrapWidth=0.9,
                    height=0.05).draw()
    win.flip()
    prop_data.to_csv(str("data/" + filename), index=True)


def start_experiment(win, mouse):
    instruction_text = visual.TextStim(
        win,
        units="norm",
        text=(
            "Your task is to move the cursor up in a straight line. Please dont lift your hand during the movement.\n\nFirst you will complete some training blocks, and then the main task will beginn.\n\nWhen the cursor is hidden, please move it back to the starting point. It will reappear and you can move it in a straight line to the top, cutting through the small cross.\n\nPress space to continue."
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


def make_thread(data_obj):
    eeg_thread = threading.Thread(
        target=bp.exampleAcquisition,
        args=(address,  # TODO: Parameter einfügen
              data_obj))
    eeg_thread.start()
    return eeg_thread


def time_scoring(y_array):
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


def stims(win):
    # SHAPES
    training_line = visual.Line(win,
                                start=(0, -1000),
                                end=(0, 1000),
                                lineWidth=5,
                                color=(0, 0, 0),
                                colorSpace='rgb255')
    beginning_point_shape = new_circle(win, beginning_point, r=touch_radius, color=(200, 200, 255))
    op_line_x = visual.Line(win,
                            start=(orientation_point[0] - 10, orientation_point[1]),
                            end=(orientation_point[0] + 10, orientation_point[1]),
                            opacity=1,
                            lineWidth=5,
                            contrast=-1.0)
    op_line_y = visual.Line(win,
                            start=(orientation_point[0], orientation_point[1] - 10),
                            end=(orientation_point[0], orientation_point[1] + 10),
                            opacity=1,
                            lineWidth=5,
                            contrast=-1.0)

    # TEXTS
    text_stim_prop_reporting = visual.TextStim(win,
                                               units="norm",
                                               text=("Before the experiment starts we will collect some baseline data.\n\nPlease move your cursor to the marked spot and then try to middle-click on the white circle.\n\nPress <space> to continue."),
                                               wrapWidth=0.9,
                                               height=0.05)
    text_stim_prop_reporting_2 = visual.TextStim(win,
                                                 units="norm",
                                                 text=("Once again we will collect some baseline data.\n\nPlease move your cursor to the marked spot and then try to middle-click on the white circle.\n\nPress <space> to continue."),
                                                 wrapWidth=0.9,
                                                 height=0.05)
    text_stim_block_complete_saving = visual.TextStim(win,
                                                      units="norm",
                                                      text=(),
                                                      wrapWidth=0.9,
                                                      height=0.05)
    text_stim_score = visual.TextStim(win,
                                      units="norm",
                                      wrapWidth=0.9,
                                      height=0.035,
                                      alignText="left")
    text_stim_feedback = visual.TextStim(win,
                                         colorSpace="rgb255",
                                         color=(255, 204, 0),
                                         units="norm",
                                         text=("For the last movement:\n\nPress <a> if you felt like force was applied to your arm during the upwards movement.\nPress <d> if you did not."),
                                         wrapWidth=0.9,
                                         height=0.05)
    text_stim_feedback_lh = visual.TextStim(win,
                                            colorSpace="rgb255",
                                            color=(255, 204, 0),
                                            units="norm",
                                            text=("For the last movement:\n\nPress <left arrow> if you felt like force was applied to your arm during the upwards movement.\nPress <right arrow> if you did not."),
                                            wrapWidth=0.9,
                                            height=0.05)
    text_stim_end = visual.TextStim(win,
                                    units="norm",
                                    text=("You have completed the experiment!\nThank you very much for your participation and have a nice day!"),
                                    wrapWidth=0.9,
                                    height=0.05)
    text_stim_entering_phase2 = visual.TextStim(win,
                                                units="norm",
                                                text=("After moving, stay where you are. \nThen middle-click on the target (your mouse is hidden).\nAfterwards, you may be asked a question that you can answer with indicated keys.\n\nPress <space> to continue."),
                                                wrapWidth=0.9,
                                                height=0.05)
    text_stim_begin = visual.TextStim(win,
                                      units="norm",
                                      text=("Training is over.\nPress <space> to begin with the experiment!"),
                                      wrapWidth=0.9,
                                      height=0.05)
    return [training_line, beginning_point_shape, op_line_x, op_line_y, text_stim_prop_reporting, text_stim_prop_reporting_2, text_stim_block_complete_saving, text_stim_score, text_stim_feedback, text_stim_feedback_lh, text_stim_end, text_stim_entering_phase2, text_stim_begin]

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
    "-t",
    "--no-training",
    default=False,
    show_default=True,
    is_flag=True,
    help="Pass to disable training sessions at the beginning",
)
@click.option(
    "-u",
    "--user",
    default="0",
    type=str,
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
)
def cli(screen: int, debug: bool, distortion: str, no_propriocept: bool, no_training: bool, user: str, lefthanded: bool):
    main(
        screen=screen,
        debug=debug,
        distortion=distortion,
        no_propriocept=no_propriocept,
        no_training=no_training,
        user=user,
        lefthanded=lefthanded
    )


if __name__ == "__main__":
    cli()
