import os
import pandas as pd
from psychopy import visual, event
import click


def main(
        screen: int = 0,
        user: str = "0",
) -> None:

    win = visual.Window(
        screen=screen,
        allowGUI=True,
        units="height",
        allowStencil=True,
        fullscr=True)

    os.makedirs("./data", exist_ok=True)
    if os.path.isfile(str("data/" + user + "_1_questionnaire.csv")):
        os.remove(str("data/" + user + "_1_questionnaire.csv"))

    # Create Form
    form = visual.Form(win, items="1_questionnaire.csv")
    form.setAutoDraw(True)

    # Wait until complete
    while True:
        win.flip()
        key = event.getKeys()
        if len(key) != 0 and key[0] == 'p' and form.complete:
            df = pd.DataFrame(form.getData())
            df[["itemText", "response"]].to_csv("data/" + user + "_1_questionnaire.csv")
            break

    win.close()


@click.command()
@click.option(
    "--user",
    default="0",
    type=str,
    show_default=True,
    help="ID of the participant",
)
def cli(user: str):
    main(
        user=user,
    )


if __name__ == "__main__":
    cli()
