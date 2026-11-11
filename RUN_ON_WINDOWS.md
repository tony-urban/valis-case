# Run on Windows

Five minutes from a fresh Windows machine to every result. Written for a person or an AI agent driving a terminal. Commands are for **PowerShell** (Start menu > type PowerShell > Windows PowerShell). They also work in Command Prompt except where noted.

## 1. Check Python

```
py --version
```

You need **Python 3.8 or later**. Nothing else: no packages, no API keys, no network after cloning.

If `py` is not found, install Python from https://www.python.org/downloads/windows/ and tick **"Add python.exe to PATH"** in the installer. Close and reopen PowerShell, then run `py --version` again.

Below, every command starts with `py`. If your machine has `python` instead (for example Python from the Microsoft Store), use `python` in place of `py`. Do not use `python3` on Windows: it often opens the Microsoft Store instead of running Python.

## 2. Get the repo

```
git clone https://github.com/tony-urban/valis-case.git
cd valis-case
```

**No git** (PowerShell says `git : The term 'git' is not recognized`)? Download the repo as a ZIP instead, in PowerShell:

```
Invoke-WebRequest https://github.com/tony-urban/valis-case/archive/refs/heads/main.zip -OutFile valis-case.zip
Expand-Archive valis-case.zip -DestinationPath .
cd valis-case-main
```

The folder is then called `valis-case-main`. The ZIP keeps the files byte for byte, so all checks pass the same way.

Every command below runs **from this folder** (the one with `README.md` in it). Paths use forward slashes: Python accepts them on Windows.

## 3. Check everything in one command

```
py tests/check.py
```

Expected last line: `83 of 83 checks passed, 0 failed, 1 skipped (see SKIP lines)`, or `84 of 84 checks passed, 0 failed` if Python 3.8 is also installed. The one optional check runs every command a second time under Python 3.8; without 3.8 it prints a SKIP line and is not counted as a pass or a fail. It takes under a minute. It runs every deliverable, resolves every citation against the raw data, recomputes every figure independently, and confirms `data/` is untouched.

If one check fails on byte comparison or checksums, see "Line endings" below.

## 4. Run each deliverable

| What | Command | Where the result is |
|---|---|---|
| Ask with sources (Q1 SaaS spend, Q2 Sales hiring) | `py ask/ask.py` | printed, and `ask/out/q1.md`, `ask/out/q2.md` |
| One question only | `py ask/ask.py --q q1` | printed |
| Value number for the CFO | `py value/value.py` | printed, and `value/VALUE_WORKSHEET.md` |
| Automation with its acceptance test | `py automation/run.py --check` | printed, and `automation/out/` |
| Pilot measurement demo (synthetic test fixture) | `py automation/run.py --data automation/demo_pilot --out $env:TEMP/pilot_demo --check --max-target-minutes 105` | printed, and that folder |
| Report to the CEO | open `answers/REPORT.md` | |

In Command Prompt, write `%TEMP%\pilot_demo` in place of `$env:TEMP/pilot_demo`.

To read a result: `notepad ask/out/q2.md`, or open the folder in VS Code.

## 5. Try a changed file

Never edit `data/`. Copy it and edit the copy:

```
Copy-Item -Recurse data $env:TEMP/mydata
notepad $env:TEMP/mydata/pnl_q1_2026.csv
py ask/ask.py --data $env:TEMP/mydata
py value/value.py --data $env:TEMP/mydata
py automation/run.py --data $env:TEMP/mydata --out $env:TEMP/myout --check
```

In Command Prompt use `xcopy /E /I data %TEMP%\mydata` for the copy. Save edited CSV files as UTF-8 (Notepad: File > Save As > Encoding: UTF-8). Excel can change dates and number formats when it saves a CSV, so prefer Notepad or VS Code.

Ideas with a known effect are in `README.md` (walkthrough map).

## Line endings

All outputs are written with LF line endings and the repo's `.gitattributes` turns off Git's line-ending conversion, so a clone gives the same bytes as on macOS and Linux. If you downloaded the ZIP and an editor saved a file with CRLF, or your Git has an override, a check may fail on byte comparison or `data/` checksums. Fix by cloning fresh with:

```
git clone -c core.autocrlf=false https://github.com/tony-urban/valis-case.git
```

## If something goes wrong

| Symptom | Fix |
|---|---|
| `git` not recognized | Use the ZIP download in step 2. |
| `py` or `python` not recognized | Step 1, and reopen PowerShell after installing. |
| `python3` opens the Microsoft Store | Use `py` instead. |
| `can't open file 'ask\ask.py'` | You are not in the repo folder. `cd` into the folder that holds `README.md`. |
| Garbled characters in the console (for example in names like Tomás) | Display only, files are correct. Run `chcp 65001` first, or open the output file in VS Code. |
| `SyntaxError` | Your Python is older than 3.8. Check `py --version`. |
| `CANNOT RUN: ...` | The data folder is missing a file or a column. The message names what it needs. |
| A check FAILs on bytes or checksums | See "Line endings". |
| Spaces in the folder path | Put the path in quotes: `--data "C:/Users/me/my data"`. |
