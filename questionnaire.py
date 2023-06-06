import os
import pandas as pd
from psychopy import visual, event
import click


def main(
        screen: int = 0,
        user: str = "0",
        form: int = 0,
) -> None:

    win = visual.Window(
        screen=screen,
        allowGUI=True,
        units="height",
        allowStencil=True,
        fullscr=True)

    os.makedirs("./data/" + user, exist_ok=True)
    # if os.path.isfile(str("data/" + user + "_" + str(form) + "_questionnaire.csv")):
    #     os.remove(str("data/" + user + "_" + str(form) + "_questionnaire.csv"))

    # Create Form
    try:
        formEl = visual.Form(win, items=str(form) + "_questionnaire.csv", size=(0.8, 0.5))
        formEl.setAutoDraw(True)
    except ValueError:
        print("ERROR: Please provide form argument! (i.e. --form 1 or 2)")
        win.close()
        return

    # Wait until complete, exit with 'p'
    while True:
        win.flip()
        key = event.getKeys()
        if len(key) != 0 and key[0] == 'p' and formEl.complete:
            df = pd.DataFrame(formEl.getData())
            df[["itemText", "response"]].to_csv("data/" + user + "/" + str(form) + "_questionnaire.csv")
            break

    win.close()


@click.command()
@click.option(
    "-u",
    "--user",
    default="0",
    type=str,
    show_default=True,
    help="ID of the participant",
)
@click.option(
    "--form",
    type=int,
    help="Number of form to be performed.",
)
def cli(user: str, form: int):
    main(
        user=user,
        form=form,
    )


if __name__ == "__main__":
    cli()
