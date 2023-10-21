# disturbed-pointing-experiment
Conducted at the Sensorimotor Control and Learning lab at TU Darmstadt (Prof. Loes van Dam) in July 2023.

## Usage
- Conda environment for experiment: experiment.yml
- before starting run `python create_monitor_file.py --width_px <px> --height_px <px>` with the specs of the monitor you are using.  
- For the questionnaires run `python questionnaire.py --form <1 or 2>`
- experiment: main.py
	- debug mode (--debug): disable fullscreen
    - no-propriocept (-n): disable baseline and trial proprioceptive reporting
    - no-training (-t): don't do any training blocks
    - user (-u): user ID
    - lefthanded (-l): save data as lefthanded
- Conda environment for the analysis: analysis.yml
