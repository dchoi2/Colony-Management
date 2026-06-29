"""Optional: fill the database with a little sample data to explore.

Run once with:  python seed_sample_data.py

This is handy for trying out the app before entering your real animals.
It does nothing if a colony named "Demo Colony" already exists.
"""
from datetime import date, timedelta

from colony_tracker import create_app, db
from colony_tracker.models import Cage, Colony, Litter, Mating, Mouse

app = create_app()

with app.app_context():
    if Colony.query.filter_by(name="Demo Colony").first():
        print("Demo data already present — nothing to do.")
    else:
        colony = Colony(
            name="Demo Colony",
            description="Sample data to explore the app.",
        )
        db.session.add(colony)
        db.session.flush()  # get colony.id

        cage_a = Cage(colony_id=colony.id, label="C-101", location="Room 2 / Rack A")
        cage_b = Cage(colony_id=colony.id, label="C-102", location="Room 2 / Rack A")
        db.session.add_all([cage_a, cage_b])
        db.session.flush()

        today = date.today()
        sire = Mouse(
            colony_id=colony.id, cage_id=cage_a.id, tag="1001", name="Max",
            sex="M", dob=today - timedelta(days=120), strain="C57BL/6J",
            genotype="Cre+/-", status="alive",
        )
        dam = Mouse(
            colony_id=colony.id, cage_id=cage_a.id, tag="1002", name="Lucy",
            sex="F", dob=today - timedelta(days=110), strain="C57BL/6J",
            genotype="fl/fl", status="alive",
        )
        db.session.add_all([sire, dam])
        db.session.flush()

        pup = Mouse(
            colony_id=colony.id, cage_id=cage_b.id, tag="1010",
            sex="F", dob=today - timedelta(days=21), strain="C57BL/6J",
            genotype="Cre+/-; fl/+", status="alive",
            sire_id=sire.id, dam_id=dam.id,
        )
        db.session.add(pup)
        db.session.flush()

        mating = Mating(
            colony_id=colony.id, sire_id=sire.id, dam_id=dam.id,
            cage_id=cage_a.id, set_up_date=today - timedelta(days=45),
            status="active",
        )
        db.session.add(mating)
        db.session.flush()

        db.session.add(Litter(
            mating_id=mating.id, dob=today - timedelta(days=21),
            num_pups=6, num_weaned=5,
        ))

        db.session.commit()
        print("Created 'Demo Colony' with sample cages, mice, and a litter.")
