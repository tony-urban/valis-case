# Run on macOS

Five minutes from a fresh Mac to every result. Written for a person or an AI agent driving a terminal.

## 1. Check Python

Open Terminal (Applications > Utilities > Terminal) and run:

```
python3 --version
```

You need **Python 3.8 or later**. Nothing else: no packages, no API keys, no network after cloning.

If the command is not found, or macOS offers to install the Command Line Developer Tools, accept that install (it ships Python 3.9), or install Python from https://www.python.org/downloads/macos/. Then run `python3 --version` again.

## 2. Get the repo

```
git clone https://github.com/tony-urban/valis-case.git
cd valis-case
```

No git? Download the ZIP from the GitHub page (Code > Download ZIP), unzip it, then `cd` into the unzipped folder.

Every command below runs **from this folder** (the one with `README.md` in it).

## 3. Check everything in one command

```
python3 tests/check.py
```

Expected last line: `81 of 81 checks passed, 0 failed, 1 skipped (see SKIP lines)`, or `82 of 82 checks passed, 0 failed` if Python 3.8 is also installed. The one optional check runs every command a second time under Python 3.8; without 3.8 it prints a SKIP line and is not counted as a pass or a fail. It takes under a minute. It runs every deliverable, resolves every citation against the raw data, recomputes every figure independently, and confirms `data/` is untouched.

## 4. Run each deliverable

| What | Command | Where the result is |
|---|---|---|
| Ask with sources (Q1 SaaS spend, Q2 Sales hiring) | `python3 ask/ask.py` | printed, and `ask/out/q1.md`, `ask/out/q2.md` |
| One question only | `python3 ask/ask.py --q q1` | printed |
| Value number for the CFO | `python3 value/value.py` | printed, and `value/VALUE_WORKSHEET.md` |
| Automation with its acceptance test | `python3 automation/run.py --check` | printed, and `automation/out/` |
| Pilot measurement demo (synthetic test fixture) | `python3 automation/run.py --data automation/demo_pilot --out /tmp/pilot_demo --check --max-target-minutes 105` | printed, and `/tmp/pilot_demo/` |
| Report to the CEO | open `answers/REPORT.md` | |

To read a result nicely: `open ask/out/q2.md` opens it in the default Markdown or text app.

## 5. Try a changed file

Never edit `data/`. Copy it and edit the copy:

```
cp -R data /tmp/mydata
open -e /tmp/mydata/pnl_q1_2026.csv        # edit in TextEdit, save as plain text
python3 ask/ask.py --data /tmp/mydata      # prints only, does not touch ask/out/
python3 value/value.py --data /tmp/mydata
python3 automation/run.py --data /tmp/mydata --out /tmp/myout --check
```

Ideas with a known effect are in `README.md` (walkthrough map).

## If something goes wrong

| Symptom | Fix |
|---|---|
| `python3: command not found` | Step 1. |
| `can't open file 'ask/ask.py'` | You are not in the repo folder. `cd` into the folder that holds `README.md`. |
| `SyntaxError` | Your Python is older than 3.8. Check `python3 --version`. |
| `CANNOT RUN: ...` | The data folder is missing a file or a column. The message names what it needs. |
| A check FAILs | The FAIL line says which check and why. Rerun the deliverable commands once, then `python3 tests/check.py` again. |
| Spaces in the folder path | Put the path in quotes: `--data "/Users/me/my data"`. |
