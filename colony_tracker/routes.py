"""Web routes (pages) for the colony tracker.

Every function below handles one URL. Functions that show a page render
an HTML template; functions that save data redirect back to a list page
and show a confirmation message.

The code is intentionally written in a plain, repetitive style so that it
is easy to read and adjust even if you are not an experienced programmer.
"""
import os
import uuid
from datetime import datetime

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)

from . import db
from .export import build_mice_workbook
from .importer import import_preview, parse_workbook
from .models import (
    EAR_TAG_SEQUENCE,
    Cage,
    Colony,
    Litter,
    Mating,
    Mouse,
    normalize_ear_tag,
)

bp = Blueprint("main", __name__)


# --------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------
def parse_date(value):
    """Turn a 'YYYY-MM-DD' string from a form into a date (or None)."""
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def parse_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def get_or_404(model, item_id):
    obj = db.session.get(model, item_id)
    if obj is None:
        from flask import abort

        abort(404)
    return obj


# --------------------------------------------------------------------------
# Dashboard
# --------------------------------------------------------------------------
@bp.route("/")
def dashboard():
    colonies = Colony.query.order_by(Colony.name).all()
    stats = {
        "colonies": Colony.query.count(),
        "mice_alive": Mouse.query.filter_by(status="alive").count(),
        "cages": Cage.query.filter_by(status="active").count(),
        "matings": Mating.query.filter_by(status="active").count(),
    }
    return render_template("dashboard.html", colonies=colonies, stats=stats)


# --------------------------------------------------------------------------
# Colonies
# --------------------------------------------------------------------------
@bp.route("/colonies")
def colony_list():
    colonies = Colony.query.order_by(Colony.name).all()
    return render_template("colonies/list.html", colonies=colonies)


@bp.route("/colonies/new", methods=["GET", "POST"])
def colony_new():
    if request.method == "POST":
        colony = Colony(
            name=request.form["name"].strip(),
            description=request.form.get("description", "").strip(),
        )
        db.session.add(colony)
        db.session.commit()
        flash(f"Colony “{colony.name}” created.", "success")
        return redirect(url_for("main.colony_detail", colony_id=colony.id))
    return render_template("colonies/form.html", colony=None)


@bp.route("/colonies/<int:colony_id>")
def colony_detail(colony_id):
    colony = get_or_404(Colony, colony_id)
    return render_template("colonies/detail.html", colony=colony)


@bp.route("/colonies/<int:colony_id>/edit", methods=["GET", "POST"])
def colony_edit(colony_id):
    colony = get_or_404(Colony, colony_id)
    if request.method == "POST":
        colony.name = request.form["name"].strip()
        colony.description = request.form.get("description", "").strip()
        db.session.commit()
        flash("Colony updated.", "success")
        return redirect(url_for("main.colony_detail", colony_id=colony.id))
    return render_template("colonies/form.html", colony=colony)


@bp.route("/colonies/<int:colony_id>/delete", methods=["POST"])
def colony_delete(colony_id):
    colony = get_or_404(Colony, colony_id)
    db.session.delete(colony)
    db.session.commit()
    flash("Colony deleted.", "success")
    return redirect(url_for("main.colony_list"))


# --------------------------------------------------------------------------
# Mice
# --------------------------------------------------------------------------
@bp.route("/mice")
def mouse_list():
    query = Mouse.query
    colony_id = request.args.get("colony", type=int)
    status = request.args.get("status")
    search = request.args.get("q", "").strip()

    if colony_id:
        query = query.filter_by(colony_id=colony_id)
    if status:
        query = query.filter_by(status=status)
    if search:
        like = f"%{search}%"
        query = query.filter(
            db.or_(
                Mouse.tag.ilike(like),
                Mouse.name.ilike(like),
                Mouse.genotype.ilike(like),
                Mouse.strain.ilike(like),
            )
        )

    mice = query.order_by(Mouse.tag).all()
    colonies = Colony.query.order_by(Colony.name).all()
    return render_template(
        "mice/list.html",
        mice=mice,
        colonies=colonies,
        colony_id=colony_id,
        status=status,
        search=search,
    )


def _mouse_form_context(mouse=None, prefill=None):
    """Shared data the add/edit mouse form needs (dropdown choices)."""
    cages = Cage.query.order_by(Cage.label).all()
    return {
        "mouse": mouse,
        "prefill": prefill or {},
        "colonies": Colony.query.order_by(Colony.name).all(),
        "cages": cages,
        "all_mice": Mouse.query.order_by(Mouse.tag).all(),
        "ear_tag_options": EAR_TAG_SEQUENCE,
        # Suggested next marker per cage, for the live hint on the form.
        "cage_next_tags": {c.id: c.next_ear_tag for c in cages},
    }


@bp.route("/mice/new", methods=["GET", "POST"])
def mouse_new():
    if request.method == "POST":
        mouse = Mouse()
        _save_mouse_from_form(mouse)
        db.session.add(mouse)
        db.session.commit()
        flash(f"Mouse “{mouse.tag}” added.", "success")
        return redirect(url_for("main.mouse_detail", mouse_id=mouse.id))

    # Adding into a specific cage? Prefill its colony and suggest the next tag.
    prefill = {}
    cage_id = request.args.get("cage", type=int)
    if cage_id:
        cage = db.session.get(Cage, cage_id)
        if cage:
            prefill = {
                "cage_id": cage.id,
                "colony_id": cage.colony_id,
                "ear_tags": cage.next_ear_tag,
            }
    return render_template("mice/form.html", **_mouse_form_context(prefill=prefill))


@bp.route("/mice/<int:mouse_id>")
def mouse_detail(mouse_id):
    mouse = get_or_404(Mouse, mouse_id)
    return render_template("mice/detail.html", mouse=mouse)


@bp.route("/mice/<int:mouse_id>/edit", methods=["GET", "POST"])
def mouse_edit(mouse_id):
    mouse = get_or_404(Mouse, mouse_id)
    if request.method == "POST":
        _save_mouse_from_form(mouse)
        db.session.commit()
        flash("Mouse updated.", "success")
        return redirect(url_for("main.mouse_detail", mouse_id=mouse.id))
    return render_template("mice/form.html", **_mouse_form_context(mouse))


@bp.route("/mice/<int:mouse_id>/delete", methods=["POST"])
def mouse_delete(mouse_id):
    mouse = get_or_404(Mouse, mouse_id)
    db.session.delete(mouse)
    db.session.commit()
    flash("Mouse deleted.", "success")
    return redirect(url_for("main.mouse_list"))


def _save_mouse_from_form(mouse):
    """Copy the submitted form fields onto a Mouse object."""
    mouse.colony_id = parse_int(request.form.get("colony_id"), None)
    mouse.cage_id = parse_int(request.form.get("cage_id"), None) or None
    mouse.tag = request.form["tag"].strip()
    mouse.name = request.form.get("name", "").strip()
    mouse.sex = request.form.get("sex", "U")
    mouse.dob = parse_date(request.form.get("dob"))
    mouse.strain = request.form.get("strain", "").strip()
    mouse.genotype = request.form.get("genotype", "").strip()
    mouse.status = request.form.get("status", "alive")
    mouse.date_of_death = parse_date(request.form.get("date_of_death"))
    mouse.sire_id = parse_int(request.form.get("sire_id"), None) or None
    mouse.dam_id = parse_int(request.form.get("dam_id"), None) or None
    mouse.ear_tags = normalize_ear_tag(request.form.get("ear_tags", ""))
    mouse.breeder_pair = request.form.get("breeder_pair", "").strip()
    mouse.parent_pair = request.form.get("parent_pair", "").strip()
    mouse.use = request.form.get("use", "").strip()
    mouse.link = request.form.get("link", "").strip()
    mouse.notes = request.form.get("notes", "").strip()


# --------------------------------------------------------------------------
# Import from Excel
# --------------------------------------------------------------------------
def _imports_dir():
    path = os.path.join(current_app.instance_path, "imports")
    os.makedirs(path, exist_ok=True)
    return path


@bp.route("/import")
def import_form():
    return render_template("import/form.html")


@bp.route("/import/preview", methods=["POST"])
def import_preview_page():
    file = request.files.get("file")
    if not file or not file.filename:
        flash("Please choose a spreadsheet file to import.", "error")
        return redirect(url_for("main.import_form"))
    if not file.filename.lower().endswith(".xlsx"):
        flash("Please upload an Excel .xlsx file.", "error")
        return redirect(url_for("main.import_form"))

    # Save to a temporary token file so the confirm step can re-read it.
    token = uuid.uuid4().hex
    saved_path = os.path.join(_imports_dir(), f"{token}.xlsx")
    file.save(saved_path)

    try:
        preview = parse_workbook(saved_path)
    except Exception as exc:  # noqa: BLE001 - show any read error to the user
        os.remove(saved_path)
        flash(f"Sorry, that file could not be read: {exc}", "error")
        return redirect(url_for("main.import_form"))

    return render_template(
        "import/preview.html",
        preview=preview,
        token=token,
        filename=file.filename,
    )


@bp.route("/import/confirm", methods=["POST"])
def import_confirm():
    token = request.form.get("token", "")
    selected = request.form.getlist("sheets")
    # Only allow our own generated token filenames (hex), never a path.
    if not token.isalnum():
        flash("That import session expired. Please upload the file again.", "error")
        return redirect(url_for("main.import_form"))
    saved_path = os.path.join(_imports_dir(), f"{token}.xlsx")
    if not os.path.exists(saved_path):
        flash("That import session expired. Please upload the file again.", "error")
        return redirect(url_for("main.import_form"))

    if not selected:
        flash("No sheets were selected, so nothing was imported.", "error")
        return redirect(url_for("main.import_form"))

    combine = request.form.get("combine") == "on"
    combined_name = request.form.get("combined_name", "").strip()

    preview = parse_workbook(saved_path)
    summaries = import_preview(
        preview, selected, combine=combine, combined_name=combined_name
    )
    os.remove(saved_path)

    total = sum(s["mice"] for s in summaries)
    flash(f"Imported {total} mice into {len(summaries)} colony(ies).", "success")
    return render_template("import/result.html", summaries=summaries)


@bp.route("/export/mice.xlsx")
def export_mice():
    """Download a formatted Excel spreadsheet of mice (optionally one colony)."""
    query = Mouse.query
    title = "Colony"
    colony_id = request.args.get("colony", type=int)
    if colony_id:
        query = query.filter_by(colony_id=colony_id)
        colony = db.session.get(Colony, colony_id)
        if colony:
            title = colony.name
    workbook = build_mice_workbook(query.all(), sheet_title=title)
    return send_file(
        workbook,
        as_attachment=True,
        download_name="colony_export.xlsx",
        mimetype=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
    )


# --------------------------------------------------------------------------
# Cages
# --------------------------------------------------------------------------
@bp.route("/cages")
def cage_list():
    colony_id = request.args.get("colony", type=int)
    query = Cage.query
    if colony_id:
        query = query.filter_by(colony_id=colony_id)
    cages = query.order_by(Cage.label).all()
    colonies = Colony.query.order_by(Colony.name).all()
    return render_template(
        "cages/list.html", cages=cages, colonies=colonies, colony_id=colony_id
    )


@bp.route("/cages/new", methods=["GET", "POST"])
def cage_new():
    if request.method == "POST":
        cage = Cage()
        _save_cage_from_form(cage)
        db.session.add(cage)
        db.session.commit()
        flash(f"Cage “{cage.label}” added.", "success")
        return redirect(url_for("main.cage_detail", cage_id=cage.id))
    colonies = Colony.query.order_by(Colony.name).all()
    return render_template("cages/form.html", cage=None, colonies=colonies)


@bp.route("/cages/<int:cage_id>")
def cage_detail(cage_id):
    cage = get_or_404(Cage, cage_id)
    return render_template("cages/detail.html", cage=cage)


@bp.route("/cages/<int:cage_id>/edit", methods=["GET", "POST"])
def cage_edit(cage_id):
    cage = get_or_404(Cage, cage_id)
    if request.method == "POST":
        _save_cage_from_form(cage)
        db.session.commit()
        flash("Cage updated.", "success")
        return redirect(url_for("main.cage_detail", cage_id=cage.id))
    colonies = Colony.query.order_by(Colony.name).all()
    return render_template("cages/form.html", cage=cage, colonies=colonies)


@bp.route("/cages/<int:cage_id>/delete", methods=["POST"])
def cage_delete(cage_id):
    cage = get_or_404(Cage, cage_id)
    db.session.delete(cage)
    db.session.commit()
    flash("Cage deleted.", "success")
    return redirect(url_for("main.cage_list"))


def _save_cage_from_form(cage):
    cage.colony_id = parse_int(request.form.get("colony_id"), None)
    cage.label = request.form["label"].strip()
    cage.location = request.form.get("location", "").strip()
    cage.status = request.form.get("status", "active")
    cage.notes = request.form.get("notes", "").strip()


# --------------------------------------------------------------------------
# Matings & litters
# --------------------------------------------------------------------------
@bp.route("/matings")
def mating_list():
    colony_id = request.args.get("colony", type=int)
    query = Mating.query
    if colony_id:
        query = query.filter_by(colony_id=colony_id)
    matings = query.order_by(Mating.set_up_date.desc()).all()
    colonies = Colony.query.order_by(Colony.name).all()
    return render_template(
        "matings/list.html",
        matings=matings,
        colonies=colonies,
        colony_id=colony_id,
    )


def _mating_form_context(mating=None):
    return {
        "mating": mating,
        "colonies": Colony.query.order_by(Colony.name).all(),
        "cages": Cage.query.order_by(Cage.label).all(),
        "males": Mouse.query.filter_by(sex="M").order_by(Mouse.tag).all(),
        "females": Mouse.query.filter_by(sex="F").order_by(Mouse.tag).all(),
    }


@bp.route("/matings/new", methods=["GET", "POST"])
def mating_new():
    if request.method == "POST":
        mating = Mating()
        _save_mating_from_form(mating)
        db.session.add(mating)
        db.session.commit()
        flash("Mating created.", "success")
        return redirect(url_for("main.mating_detail", mating_id=mating.id))
    return render_template("matings/form.html", **_mating_form_context())


@bp.route("/matings/<int:mating_id>")
def mating_detail(mating_id):
    mating = get_or_404(Mating, mating_id)
    return render_template("matings/detail.html", mating=mating)


@bp.route("/matings/<int:mating_id>/edit", methods=["GET", "POST"])
def mating_edit(mating_id):
    mating = get_or_404(Mating, mating_id)
    if request.method == "POST":
        _save_mating_from_form(mating)
        db.session.commit()
        flash("Mating updated.", "success")
        return redirect(url_for("main.mating_detail", mating_id=mating.id))
    return render_template("matings/form.html", **_mating_form_context(mating))


@bp.route("/matings/<int:mating_id>/delete", methods=["POST"])
def mating_delete(mating_id):
    mating = get_or_404(Mating, mating_id)
    db.session.delete(mating)
    db.session.commit()
    flash("Mating deleted.", "success")
    return redirect(url_for("main.mating_list"))


def _save_mating_from_form(mating):
    mating.colony_id = parse_int(request.form.get("colony_id"), None)
    mating.sire_id = parse_int(request.form.get("sire_id"), None) or None
    mating.dam_id = parse_int(request.form.get("dam_id"), None) or None
    mating.cage_id = parse_int(request.form.get("cage_id"), None) or None
    mating.set_up_date = parse_date(request.form.get("set_up_date"))
    mating.status = request.form.get("status", "active")
    mating.notes = request.form.get("notes", "").strip()


@bp.route("/matings/<int:mating_id>/litters/new", methods=["POST"])
def litter_new(mating_id):
    mating = get_or_404(Mating, mating_id)
    litter = Litter(
        mating_id=mating.id,
        dob=parse_date(request.form.get("dob")),
        num_pups=parse_int(request.form.get("num_pups"), 0),
        num_weaned=parse_int(request.form.get("num_weaned"), 0),
        notes=request.form.get("notes", "").strip(),
    )
    db.session.add(litter)
    db.session.commit()
    flash("Litter recorded.", "success")
    return redirect(url_for("main.mating_detail", mating_id=mating.id))


@bp.route("/litters/<int:litter_id>/delete", methods=["POST"])
def litter_delete(litter_id):
    litter = get_or_404(Litter, litter_id)
    mating_id = litter.mating_id
    db.session.delete(litter)
    db.session.commit()
    flash("Litter deleted.", "success")
    return redirect(url_for("main.mating_detail", mating_id=mating_id))
