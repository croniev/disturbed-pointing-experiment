# disturbed-pointing-experiment
Idea for my Bachelors Thesis. 
Please do not clone if you are planning on participating in the experiment!!

## Usage
- Conda Environment for Handeln course should work. If not install from yml file.
- For the questionnaires run `python questionnaire.py --form <1 or 2>`
- before starting run `python create_monitor_file.py --width_px <px> --height_px <px>` with the specs of the monitor you are using.  
- make sure the bioPLUX device is connected via bluetooth and the mac address is written into the params.json file.
- run main.py
	- debug: disable fullscreen
    - no_propriocept (-n): disable baseline and trial proprioceptive reporting
    - no_training (-t): don't do any training blocks
    - user: user ID
    - lefthanded: save data as lefthanded
