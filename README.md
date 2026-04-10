# MIDI Reaction Trainer

A desktop app that improves note and chord muscle memory by showing random targets and timing how quickly you play them on a MIDI keyboard.

## Features
- **Single Note Mode** — random notes from selected key(s), pitch-class matching
- **Chord Mode** — diatonic triads (major/minor/diminished), root position only
- **Inversion Drill** — prompts specify the inversion (root, 1st, 2nd) you must play
- **Key Filtering** — select one or more keys; targets are drawn only from those scales
- **Reaction Timing** — measures time from prompt to correct input
- **Session Stats** — accuracy, avg/median/fastest/slowest reaction time, streaks
- **Session History** — saved as JSON files in `~/.midi_trainer/history/`

## Requirements
- Python 3.11+
- A MIDI keyboard connected to your computer
- Windows (tested), macOS/Linux should also work

## Setup

```bash
pip install pipenv
cd "MIDI Trainer"
pipenv install
```

## Run

```bash
pipenv run python -m src.main
```

## Run Tests

```bash
pipenv run pytest tests/ -v
```

## Project Structure

```
src/
├── main.py              # Entry point, Dear PyGui app
├── midi_input.py        # MIDI device management
├── theory.py            # Music theory engine
├── exercise.py          # Session state machine & validation
├── scoring.py           # Statistics computation
├── history.py           # JSON session persistence
└── ui/
    ├── setup_screen.py    # Configuration screen
    ├── practice_screen.py # Live drill screen
    └── results_screen.py  # Results & history screen
```
