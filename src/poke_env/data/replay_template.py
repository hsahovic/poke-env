import os

with open(
    os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "static", "replay_template.html"
    )
) as f:
    REPLAY_TEMPLATE = f.read()
