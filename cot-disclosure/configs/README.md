# configs/

Settings the code reads. Nothing here is a result.

- `models.yaml`: the models we use, their provider and the Voyager IDs they map to.
- `trackB.yaml`: Track B's design (models, conditions, settings).
- `prices.yaml`: provider prices (unused: the project made no paid calls).
- `canary/`: reference texts for the identity canary, which checks that a served model is the one we asked for.
- `path_allowlist.txt`: which paths each teammate's branch may change. `tools/path_check.py` enforces it in a git hook.
- `team_identities.txt`: the team's commit identities, as hashes (the repo is public, so no emails).

Open `models.yaml` first. Change a file here only if you know which code reads it.
