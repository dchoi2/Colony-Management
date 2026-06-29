# 🐭 Colony Management Tracker

A simple, browser-based tool for tracking laboratory mouse colonies —
inspired by SoftMouse. It runs on your own computer, stores everything in a
local database file, and gives non-technical lab staff an easy interface to
record and update animals, cages, breeding, and litters.

No programming knowledge is needed to **use** it: you start the app once,
then everyone works through normal web pages in a browser.

## What you can track

- **Colonies** — top-level groups of animals (a lab, project, or line)
- **Mice** — ear tag/ID, name, sex, date of birth, strain, genotype, status,
  cage, and parents (sire & dam) for genealogy
- **Cages** — housing units, location, and who lives in them
- **Matings** — breeding pairs (sire × dam)
- **Litters** — births recorded against each mating (pups born, pups weaned)

Plus a **dashboard** with live counts and **search/filter** for finding mice
by tag, name, genotype, strain, colony, or status.

## Requirements

- Python 3.9 or newer

## Setup (one time)

```bash
# 1. Install the dependencies
pip install -r requirements.txt

# 2. (Optional) add sample data so you can explore first
python seed_sample_data.py
```

## Running the app

```bash
python run.py
```

Then open **http://127.0.0.1:5000** in any web browser. Leave the terminal
window open while you use the app; close it (Ctrl+C) when you're done.

All your data is saved automatically in a file called `colony.db` in this
folder. To back up your data, just copy that file somewhere safe.

## How the project is organized

```
run.py                     # start the app
seed_sample_data.py        # optional demo data
requirements.txt           # Python dependencies
colony_tracker/
  __init__.py              # app setup + database connection
  models.py                # the database tables (Colony, Mouse, Cage, ...)
  routes.py                # the pages and what each one does
  templates/               # the HTML pages you see in the browser
  static/style.css         # the look and feel
```

If you want to change wording, add a field, or adjust the layout, those are
the files to edit. The code is written in a plain, well-commented style to
make that approachable.

## Notes

- This stores data in a single SQLite file — perfect for one lab/computer.
  For multi-user network access you'd later move to a shared database
  (e.g. PostgreSQL); the structure here is ready to grow into that.
- This is a starting MVP. Natural next steps: genotyping records, weaning
  workflows, CSV import/export, multi-generation pedigree charts, and user
  logins.
