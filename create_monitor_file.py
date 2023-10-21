"""
Create a PsychoPy monitor profile and validate it visually.

python create_monitor_profile.py --help for usage and further description. Can use prompts, or pass arguments in cli:

python wahrnehmung_seminar/create_monitor_profile.py --width 62 --distance 65 --gamma 1.85 --width_px 1920 --height_px 1080
"""
import click
from psychopy import prefs, core, monitors
# to avoid bug on windows (https://www.psychopy.org/troubleshooting.html#errors-with-getting-setting-the-gamma-ramp)
prefs.general["gammaErrorPolicy"] = "warn"


@click.command()
@click.option(
    "--width_px",
    help="Width in pixels",
    prompt="Enter the monitor width in pixels (see determine_fullscreen_pixels.py)",
    type=float,
)
@click.option(
    "--height_px",
    help="Height in pixels",
    prompt="Enter the monitor height in pixels (see determine_fullscreen_pixels.py)",
    type=float,
)
def main(
    width_px: float,
    height_px: float,
    screen: int = 0,
    screenshot: bool = False
):
    monitor_disturbed_pointing = monitors.Monitor(
        "monitor_disturbed_pointing",
        notes="Monitor set up for the experiment of Levins Bachelor.",
    )

    monitor_disturbed_pointing.setSizePix((width_px, height_px))

    # save monitor out:
    monitor_disturbed_pointing.save()
    print("monitor has been saved")
    core.quit()


if __name__ == "__main__":
    main()
