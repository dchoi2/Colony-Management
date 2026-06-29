"""Database models for the colony tracker.

The data model mirrors how a real mouse colony is organized:

    Colony  -- a project or research group's collection of animals
      |
      +-- Cage    -- a physical housing unit within the colony
      |     |
      |     +-- Mouse  -- an individual animal, optionally housed in a cage
      |
      +-- Mating  -- a breeding pair (a sire and a dam)
            |
            +-- Litter -- offspring produced by a mating

Each Mouse can also point back to its own sire and dam, which lets us
track genealogy (who is the parent of whom).
"""
from datetime import date, datetime

from . import db


class Colony(db.Model):
    """A colony: the top-level grouping of animals (e.g. a lab or project)."""

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    cages = db.relationship(
        "Cage", backref="colony", cascade="all, delete-orphan"
    )
    mice = db.relationship(
        "Mouse", backref="colony", cascade="all, delete-orphan"
    )
    matings = db.relationship(
        "Mating", backref="colony", cascade="all, delete-orphan"
    )

    @property
    def living_mice(self):
        return [m for m in self.mice if m.status == "alive"]


class Cage(db.Model):
    """A physical cage that houses one or more mice."""

    id = db.Column(db.Integer, primary_key=True)
    colony_id = db.Column(
        db.Integer, db.ForeignKey("colony.id"), nullable=False
    )
    label = db.Column(db.String(60), nullable=False)  # e.g. "C-101"
    location = db.Column(db.String(120), default="")  # room / rack / shelf
    status = db.Column(db.String(20), default="active")  # active / retired
    notes = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    mice = db.relationship("Mouse", backref="cage")

    @property
    def occupant_count(self):
        return len([m for m in self.mice if m.status == "alive"])


class Mouse(db.Model):
    """An individual animal."""

    id = db.Column(db.Integer, primary_key=True)
    colony_id = db.Column(
        db.Integer, db.ForeignKey("colony.id"), nullable=False
    )
    cage_id = db.Column(db.Integer, db.ForeignKey("cage.id"), nullable=True)

    # Identification
    tag = db.Column(db.String(60), nullable=False)  # ear tag / animal ID
    name = db.Column(db.String(120), default="")
    sex = db.Column(db.String(1), default="U")  # M / F / U (unknown)

    # Biology
    dob = db.Column(db.Date, nullable=True)  # date of birth
    strain = db.Column(db.String(120), default="")
    genotype = db.Column(db.String(120), default="")
    status = db.Column(db.String(20), default="alive")  # alive/dead/weaned/...
    date_of_death = db.Column(db.Date, nullable=True)

    # Genealogy: this mouse's parents (other Mouse rows in the same table).
    sire_id = db.Column(db.Integer, db.ForeignKey("mouse.id"), nullable=True)
    dam_id = db.Column(db.Integer, db.ForeignKey("mouse.id"), nullable=True)

    # Extra fields that mirror common lab colony spreadsheets (all optional).
    ear_tags = db.Column(db.String(40), default="")      # e.g. rt / lt / both
    breeder_pair = db.Column(db.String(60), default="")  # e.g. b24
    parent_pair = db.Column(db.String(120), default="")  # e.g. wf/hm
    use = db.Column(db.String(200), default="")          # e.g. used in FC behavior
    link = db.Column(db.String(300), default="")         # related file or URL

    notes = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    sire = db.relationship(
        "Mouse", remote_side=[id], foreign_keys=[sire_id], backref="sired"
    )
    dam = db.relationship(
        "Mouse", remote_side=[id], foreign_keys=[dam_id], backref="bore"
    )

    @property
    def age_days(self):
        """Age in days, or None if the date of birth is unknown."""
        if not self.dob:
            return None
        end = self.date_of_death or date.today()
        return (end - self.dob).days

    @property
    def age_weeks(self):
        """Whole weeks of age, matching the 'age' column in lab spreadsheets."""
        days = self.age_days
        return None if days is None else days // 7

    @property
    def age_display(self):
        """Human-friendly age such as '5w 2d' or '3d'."""
        days = self.age_days
        if days is None:
            return "—"
        weeks, rem = divmod(days, 7)
        if weeks:
            return f"{weeks}w {rem}d"
        return f"{rem}d"

    @property
    def sex_display(self):
        return {"M": "Male", "F": "Female"}.get(self.sex, "Unknown")


class Mating(db.Model):
    """A breeding pair set up to produce litters."""

    id = db.Column(db.Integer, primary_key=True)
    colony_id = db.Column(
        db.Integer, db.ForeignKey("colony.id"), nullable=False
    )
    sire_id = db.Column(db.Integer, db.ForeignKey("mouse.id"), nullable=True)
    dam_id = db.Column(db.Integer, db.ForeignKey("mouse.id"), nullable=True)
    cage_id = db.Column(db.Integer, db.ForeignKey("cage.id"), nullable=True)

    set_up_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(20), default="active")  # active / ended
    notes = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    sire = db.relationship("Mouse", foreign_keys=[sire_id])
    dam = db.relationship("Mouse", foreign_keys=[dam_id])
    cage = db.relationship("Cage", foreign_keys=[cage_id])
    litters = db.relationship(
        "Litter", backref="mating", cascade="all, delete-orphan"
    )


class Litter(db.Model):
    """Offspring produced by a mating."""

    id = db.Column(db.Integer, primary_key=True)
    mating_id = db.Column(
        db.Integer, db.ForeignKey("mating.id"), nullable=False
    )
    dob = db.Column(db.Date, nullable=True)  # birth date of the litter
    num_pups = db.Column(db.Integer, default=0)
    num_weaned = db.Column(db.Integer, default=0)
    notes = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
