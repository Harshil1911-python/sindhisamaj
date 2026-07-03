"""
Sindhi Samaj Pariwar Surat - Marriage Bureau Software
Flask backend. All templates/static files are loose in this same folder
(no subfolders), as requested. Uses SQLite as the database.
"""

import os
import io
import csv
import uuid
import sqlite3
import secrets
from datetime import datetime, date
from functools import wraps

from flask import (
    Flask, request, jsonify, session, send_file, send_from_directory,
    redirect, url_for, g, abort, Response
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# DATA_DIR can be pointed at a Render persistent disk mount so the database
# and uploaded photos survive redeploys. Defaults to the app folder itself.
DATA_DIR = os.environ.get("DATA_DIR", BASE_DIR)
os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(DATA_DIR, "database.db")
UPLOAD_DIR = os.path.join(DATA_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_IMAGE_EXT = {"png", "jpg", "jpeg", "webp", "gif"}
ALLOWED_DOC_EXT = {"pdf"}
ALLOWED_DB_EXT = {"db", "sqlite", "sqlite3"}

app = Flask(__name__, template_folder=BASE_DIR, static_folder=BASE_DIR, static_url_path="")
app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(32))
app.config["MAX_CONTENT_LENGTH"] = 60 * 1024 * 1024  # 60 MB uploads ceiling

# ---------------------------------------------------------------------------
# All profile fields (order matters for CSV export/import & forms)
# ---------------------------------------------------------------------------
PROFILE_FIELDS = [
    "full_name", "gender", "profile_for", "father_name", "mother_name", "guardian_name",
    "dob", "time_of_birth", "place_of_birth", "age", "height", "weight", "blood_group",
    "complexion", "body_type", "nationality", "religion", "community", "sindhi_caste",
    "sub_caste", "mother_tongue",
    "marital_status", "children",
    "occupation", "career", "company", "business", "designation", "income_monthly", "income_yearly",
    "qualification", "college", "university",
    "current_city", "native_place", "phone", "alternate_phone", "email", "whatsapp",
    "emergency_contact", "permanent_address", "temporary_address",
    "food_preference", "smoking", "drinking", "habits", "hobbies", "interests",
    "languages_known", "about_yourself",
    "expected_age", "expected_height", "expected_education", "expected_profession",
    "expected_income", "expected_location", "expected_lifestyle",
    "manglik", "rashi", "nakshatra", "mulank", "kundli_available", "birth_chart", "horoscope_notes",
    "disability", "special_notes",
    "aadhar_number", "passport_number",
]

FILE_FIELDS = ["kundli_pdf", "aadhar_photo", "passport_photo"]  # single-file inputs
GALLERY_FIELD = "photos"  # multi-file input (profile photos)


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    first_time = not os.path.exists(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    with open(os.path.join(BASE_DIR, "schema.sql"), "r") as f:
        conn.executescript(f.read())
    # create a default admin if none exists yet
    cur = conn.execute("SELECT COUNT(*) FROM admins")
    if cur.fetchone()[0] == 0:
        conn.execute(
            "INSERT INTO admins (username, password_hash) VALUES (?, ?)",
            ("admin", generate_password_hash("admin123")),
        )
        conn.commit()
        print("=" * 70)
        print(" Default admin created -> username: admin | password: admin123")
        print(" Please sign in and change this immediately.")
        print("=" * 70)
    conn.commit()
    conn.close()
    return first_time


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------
def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("admin_id"):
            if request.path.startswith("/api/") or request.path.startswith("/export") \
                    or request.path.startswith("/import") or request.path.startswith("/backup") \
                    or request.path.startswith("/restore") or request.path.startswith("/biodata"):
                return jsonify({"success": False, "message": "Not authenticated"}), 401
            return redirect("/signin.html")
        return view(*args, **kwargs)
    return wrapped


def allowed_ext(filename, allowed):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed


def save_upload(file_storage, subfolder_prefix):
    if not file_storage or file_storage.filename == "":
        return None
    ext = file_storage.filename.rsplit(".", 1)[-1].lower() if "." in file_storage.filename else ""
    fname = f"{subfolder_prefix}_{uuid.uuid4().hex[:10]}.{ext}" if ext else f"{subfolder_prefix}_{uuid.uuid4().hex[:10]}"
    fname = secure_filename(fname)
    path = os.path.join(UPLOAD_DIR, fname)
    file_storage.save(path)
    return fname  # stored relative to /uploads/


def calc_age(dob_str):
    try:
        y, m, d = [int(x) for x in dob_str.split("-")]
        born = date(y, m, d)
        today = date.today()
        return today.year - born.year - ((today.month, today.day) < (born.month, born.day))
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Static page routes (all pages are plain html files loose in this folder)
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    return send_from_directory(BASE_DIR, "landing.html")


@app.route("/landing.html")
def landing_page():
    return send_from_directory(BASE_DIR, "landing.html")


@app.route("/register.html")
def register_page():
    return send_from_directory(BASE_DIR, "register.html")


@app.route("/signin.html")
def signin_page():
    return send_from_directory(BASE_DIR, "signin.html")


@app.route("/admin.html")
@login_required
def admin_page():
    return send_from_directory(BASE_DIR, "admin.html")


@app.route("/view.html")
@login_required
def view_page():
    return send_from_directory(BASE_DIR, "view.html")


@app.route("/details.html")
def details_page():
    # Public read-only page (also the QR destination). No admin functions here.
    return send_from_directory(BASE_DIR, "details.html")


@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_DIR, filename)


# ---------------------------------------------------------------------------
# Auth API
# ---------------------------------------------------------------------------
@app.route("/signin", methods=["POST"])
def signin():
    data = request.get_json(silent=True) or request.form
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    db = get_db()
    row = db.execute("SELECT * FROM admins WHERE username = ?", (username,)).fetchone()
    if row and check_password_hash(row["password_hash"], password):
        session["admin_id"] = row["id"]
        session["admin_username"] = row["username"]
        return jsonify({"success": True, "redirect": "/admin.html"})
    return jsonify({"success": False, "message": "Invalid username or password"}), 401


@app.route("/signout", methods=["POST"])
def signout():
    session.clear()
    return jsonify({"success": True})


@app.route("/api/me")
def api_me():
    if session.get("admin_id"):
        return jsonify({"authenticated": True, "username": session.get("admin_username")})
    return jsonify({"authenticated": False})


@app.route("/change-password", methods=["POST"])
@login_required
def change_password():
    data = request.get_json(silent=True) or request.form
    current = data.get("current_password") or ""
    new = data.get("new_password") or ""
    db = get_db()
    row = db.execute("SELECT * FROM admins WHERE id = ?", (session["admin_id"],)).fetchone()
    if not row or not check_password_hash(row["password_hash"], current):
        return jsonify({"success": False, "message": "Current password is incorrect"}), 400
    if len(new) < 6:
        return jsonify({"success": False, "message": "New password must be at least 6 characters"}), 400
    db.execute("UPDATE admins SET password_hash = ? WHERE id = ?", (generate_password_hash(new), row["id"]))
    db.commit()
    return jsonify({"success": True})


@app.route("/create-admin", methods=["POST"])
@login_required
def create_admin():
    data = request.get_json(silent=True) or request.form
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    if not username or len(password) < 6:
        return jsonify({"success": False, "message": "Username required & password min 6 chars"}), 400
    db = get_db()
    try:
        db.execute("INSERT INTO admins (username, password_hash) VALUES (?, ?)",
                   (username, generate_password_hash(password)))
        db.commit()
    except sqlite3.IntegrityError:
        return jsonify({"success": False, "message": "Username already exists"}), 400
    return jsonify({"success": True})


# ---------------------------------------------------------------------------
# Public registration
# ---------------------------------------------------------------------------
@app.route("/register", methods=["POST"])
def register():
    form = request.form
    if not form.get("full_name") or not form.get("phone") or not form.get("email"):
        return jsonify({"success": False, "message": "Please fill all required fields."}), 400

    db = get_db()
    cols, vals, marks = [], [], []
    for field in PROFILE_FIELDS:
        cols.append(field)
        v = form.get(field, "")
        if field == "age" and not v:
            v = calc_age(form.get("dob", "")) or None
        vals.append(v)
        marks.append("?")

    # password (optional, hashed if provided)
    pw = form.get("password") or ""
    cols.append("password_hash")
    vals.append(generate_password_hash(pw) if pw else None)
    marks.append("?")

    # file uploads (single)
    for f in FILE_FIELDS:
        saved = save_upload(request.files.get(f), f)
        col = f + "_path" if f != "kundli_pdf" else "kundli_pdf_path"
        cols.append(col)
        vals.append(saved)
        marks.append("?")

    token = uuid.uuid4().hex
    cols.append("public_token")
    vals.append(token)
    marks.append("?")

    sql = f"INSERT INTO profiles ({', '.join(cols)}) VALUES ({', '.join(marks)})"
    cur = db.execute(sql, vals)
    profile_id = cur.lastrowid

    # gallery photos (multiple)
    files = request.files.getlist("photos")
    for i, fs in enumerate(files):
        if fs and fs.filename and allowed_ext(fs.filename, ALLOWED_IMAGE_EXT):
            saved = save_upload(fs, f"gallery_{profile_id}")
            db.execute(
                "INSERT INTO photos (profile_id, filepath, is_primary, sort_order) VALUES (?, ?, ?, ?)",
                (profile_id, saved, 1 if i == 0 else 0, i),
            )

    db.commit()
    return jsonify({"success": True, "profile_id": profile_id})


# ---------------------------------------------------------------------------
# Profiles API (admin + public detail)
# ---------------------------------------------------------------------------
def row_to_dict(row):
    d = dict(row)
    return d


def attach_photos(db, profile):
    rows = db.execute(
        "SELECT id, filepath, is_primary FROM photos WHERE profile_id = ? ORDER BY sort_order ASC",
        (profile["id"],),
    ).fetchall()
    profile["photos"] = [f"/uploads/{r['filepath']}" for r in rows]
    profile["primary_photo"] = profile["photos"][0] if profile["photos"] else None
    for f in ["kundli_pdf_path", "aadhar_photo_path", "passport_photo_path"]:
        if profile.get(f):
            profile[f] = f"/uploads/{profile[f]}"
    return profile


@app.route("/api/profiles")
@login_required
def api_profiles():
    db = get_db()
    q = "SELECT * FROM profiles WHERE 1=1"
    args = []

    def add_eq(param, col):
        nonlocal q
        val = request.args.get(param)
        if val:
            q_local = f" AND {col} = ?"
            return q_local, val
        return "", None

    filters = {
        "gender": "gender", "profile_for": "profile_for", "marital_status": "marital_status",
        "current_city": "current_city", "native_place": "native_place",
        "sindhi_caste": "sindhi_caste", "sub_caste": "sub_caste",
        "manglik": "manglik", "food_preference": "food_preference",
        "smoking": "smoking", "drinking": "drinking", "blood_group": "blood_group",
        "complexion": "complexion", "body_type": "body_type", "status": "status",
        "qualification": "qualification", "occupation": "occupation",
    }
    for param, col in filters.items():
        val = request.args.get(param)
        if val:
            q += f" AND {col} = ?"
            args.append(val)

    age_min = request.args.get("age_min")
    age_max = request.args.get("age_max")
    if age_min:
        q += " AND age >= ?"
        args.append(age_min)
    if age_max:
        q += " AND age <= ?"
        args.append(age_max)

    search = request.args.get("search")
    if search:
        q += " AND (full_name LIKE ? OR phone LIKE ? OR email LIKE ? OR occupation LIKE ?)"
        like = f"%{search}%"
        args.extend([like, like, like, like])

    q += " ORDER BY created_at DESC"
    rows = db.execute(q, args).fetchall()
    profiles = [attach_photos(db, row_to_dict(r)) for r in rows]
    return jsonify({"success": True, "count": len(profiles), "profiles": profiles})


@app.route("/api/filter-options")
@login_required
def api_filter_options():
    db = get_db()
    cols = ["current_city", "native_place", "sindhi_caste", "sub_caste", "marital_status",
            "qualification", "occupation", "blood_group", "complexion", "body_type",
            "food_preference", "manglik"]
    options = {}
    for c in cols:
        rows = db.execute(f"SELECT DISTINCT {c} FROM profiles WHERE {c} IS NOT NULL AND {c} != '' ORDER BY {c}").fetchall()
        options[c] = [r[0] for r in rows]
    return jsonify({"success": True, "options": options})


@app.route("/api/profile/<int:profile_id>")
@login_required
def api_profile_detail(profile_id):
    db = get_db()
    row = db.execute("SELECT * FROM profiles WHERE id = ?", (profile_id,)).fetchone()
    if not row:
        abort(404)
    return jsonify({"success": True, "profile": attach_photos(db, row_to_dict(row))})


@app.route("/api/public/profile")
def api_public_profile():
    """Used by details.html (QR destination) - read-only, token-gated, no sensitive admin data."""
    token = request.args.get("token")
    pid = request.args.get("id")
    db = get_db()
    if token:
        row = db.execute("SELECT * FROM profiles WHERE public_token = ?", (token,)).fetchone()
    elif pid and session.get("admin_id"):
        row = db.execute("SELECT * FROM profiles WHERE id = ?", (pid,)).fetchone()
    else:
        return jsonify({"success": False, "message": "Missing token"}), 400
    if not row:
        abort(404)
    profile = attach_photos(db, row_to_dict(row))
    # strip sensitive verification data from the public view
    for f in ["aadhar_number", "aadhar_photo_path", "passport_number", "passport_photo_path",
              "password_hash", "public_token"]:
        profile.pop(f, None)
    return jsonify({"success": True, "profile": profile})


@app.route("/api/profile/<int:profile_id>", methods=["PUT"])
@login_required
def api_profile_update(profile_id):
    data = request.get_json(silent=True) or {}
    db = get_db()
    allowed_cols = set(PROFILE_FIELDS) | {"status"}
    sets, vals = [], []
    for k, v in data.items():
        if k in allowed_cols:
            sets.append(f"{k} = ?")
            vals.append(v)
    if not sets:
        return jsonify({"success": False, "message": "Nothing to update"}), 400
    sets.append("updated_at = ?")
    vals.append(datetime.utcnow().isoformat())
    vals.append(profile_id)
    db.execute(f"UPDATE profiles SET {', '.join(sets)} WHERE id = ?", vals)
    db.commit()
    return jsonify({"success": True})


@app.route("/api/profile/<int:profile_id>", methods=["DELETE"])
@login_required
def api_profile_delete(profile_id):
    db = get_db()
    db.execute("DELETE FROM profiles WHERE id = ?", (profile_id,))
    db.commit()
    return jsonify({"success": True})


@app.route("/api/profile/<int:profile_id>/qr.png")
def api_profile_qr(profile_id):
    import qrcode
    db = get_db()
    row = db.execute("SELECT public_token FROM profiles WHERE id = ?", (profile_id,)).fetchone()
    if not row:
        abort(404)
    base = request.url_root.rstrip("/")
    target = f"{base}/details.html?token={row['public_token']}"
    img = qrcode.make(target)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return send_file(buf, mimetype="image/png")


# ---------------------------------------------------------------------------
# CSV Import / Export
# ---------------------------------------------------------------------------
@app.route("/export/csv")
@login_required
def export_csv():
    db = get_db()
    rows = db.execute("SELECT * FROM profiles ORDER BY created_at DESC").fetchall()
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=PROFILE_FIELDS)
    writer.writeheader()
    for r in rows:
        d = dict(r)
        writer.writerow({k: d.get(k, "") for k in PROFILE_FIELDS})
    mem = io.BytesIO(output.getvalue().encode("utf-8-sig"))
    fname = f"profiles_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return send_file(mem, mimetype="text/csv", as_attachment=True, download_name=fname)


@app.route("/import/csv", methods=["POST"])
@login_required
def import_csv():
    file = request.files.get("file")
    if not file or not file.filename.lower().endswith(".csv"):
        return jsonify({"success": False, "message": "Please upload a .csv file"}), 400
    stream = io.StringIO(file.stream.read().decode("utf-8-sig"))
    reader = csv.DictReader(stream)
    db = get_db()
    inserted = 0
    for row in reader:
        cols, vals, marks = [], [], []
        for field in PROFILE_FIELDS:
            cols.append(field)
            vals.append(row.get(field, ""))
            marks.append("?")
        cols.append("public_token")
        vals.append(uuid.uuid4().hex)
        marks.append("?")
        db.execute(f"INSERT INTO profiles ({', '.join(cols)}) VALUES ({', '.join(marks)})", vals)
        inserted += 1
    db.commit()
    return jsonify({"success": True, "inserted": inserted})


# ---------------------------------------------------------------------------
# Backup / Restore
# ---------------------------------------------------------------------------
@app.route("/backup")
@login_required
def backup_db():
    fname = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    return send_file(DB_PATH, as_attachment=True, download_name=fname)


@app.route("/restore", methods=["POST"])
@login_required
def restore_db():
    file = request.files.get("file")
    if not file or not allowed_ext(file.filename, ALLOWED_DB_EXT):
        return jsonify({"success": False, "message": "Please upload a valid .db backup file"}), 400
    close_db()
    file.save(DB_PATH)
    return jsonify({"success": True})


# ---------------------------------------------------------------------------
# Biodata generation (PDF & PNG)
# ---------------------------------------------------------------------------
def biodata_lines(profile):
    def g(k, label=None):
        v = profile.get(k)
        return (label or k.replace("_", " ").title(), v if v not in (None, "") else "-")

    sections = [
        ("Basic Information", [
            g("full_name", "Full Name"), g("gender", "Gender"), g("dob", "Date of Birth"),
            g("age", "Age"), g("height", "Height"), g("complexion", "Complexion"),
            g("marital_status", "Marital Status"), g("father_name", "Father's Name"),
            g("mother_name", "Mother's Name"), g("sindhi_caste", "Sindhi Caste"),
            g("mother_tongue", "Mother Tongue"),
        ]),
        ("Education & Career", [
            g("qualification", "Qualification"), g("occupation", "Occupation"),
            g("company", "Company"), g("designation", "Designation"),
            g("income_yearly", "Annual Income"),
        ]),
        ("Contact & Address", [
            g("current_city", "Current City"), g("native_place", "Native Place"),
            g("phone", "Phone"), g("email", "Email"),
        ]),
        ("Astrological Details", [
            g("manglik", "Manglik"), g("rashi", "Rashi"), g("nakshatra", "Nakshatra"),
        ]),
        ("About", [g("about_yourself", "About")]),
    ]
    return sections


@app.route("/biodata/<int:profile_id>/pdf")
@login_required
def biodata_pdf(profile_id):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib.colors import HexColor
    from reportlab.pdfgen import canvas as pdfcanvas

    db = get_db()
    row = db.execute("SELECT * FROM profiles WHERE id = ?", (profile_id,)).fetchone()
    if not row:
        abort(404)
    profile = attach_photos(db, row_to_dict(row))

    buf = io.BytesIO()
    c = pdfcanvas.Canvas(buf, pagesize=A4)
    width, height = A4
    gold = HexColor("#c9972b")
    indigo = HexColor("#1b3a63")
    maroon = HexColor("#8b1e3f")
    ink = HexColor("#14161f")

    c.setFillColor(maroon)
    c.rect(0, height - 14 * mm, width, 14 * mm, fill=1, stroke=0)
    c.setFillColor(HexColor("#f6f0e4"))
    c.setFont("Helvetica-Bold", 16)
    c.drawString(18 * mm, height - 10 * mm, "Sindhi Samaj Pariwar Surat — Marriage Biodata")

    y = height - 26 * mm

    # photo
    photo_path = None
    if profile["photos"]:
        photo_path = os.path.join(UPLOAD_DIR, profile["photos"][0].split("/uploads/")[-1])
    if photo_path and os.path.exists(photo_path):
        try:
            c.drawImage(photo_path, width - 55 * mm, y - 45 * mm, width=40 * mm, height=48 * mm,
                        preserveAspectRatio=True, anchor='n')
        except Exception:
            pass

    c.setFillColor(indigo)
    c.setFont("Helvetica-Bold", 20)
    c.drawString(18 * mm, y, profile.get("full_name") or "Unnamed Profile")
    y -= 10 * mm

    for section_title, rows in biodata_lines(profile):
        if y < 25 * mm:
            c.showPage()
            y = height - 20 * mm
        c.setFillColor(gold)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(18 * mm, y, section_title)
        y -= 6 * mm
        c.setStrokeColor(gold)
        c.line(18 * mm, y + 2 * mm, width - 18 * mm, y + 2 * mm)
        c.setFont("Helvetica", 10)
        for label, val in rows:
            if y < 20 * mm:
                c.showPage()
                y = height - 20 * mm
            c.setFillColor(ink)
            text = f"{label}: {val}"
            for line in _wrap_text(text, 100):
                c.drawString(20 * mm, y, line)
                y -= 5.2 * mm
        y -= 3 * mm

    c.save()
    buf.seek(0)
    fname = f"biodata_{secure_filename(profile.get('full_name') or str(profile_id))}.pdf"
    return send_file(buf, mimetype="application/pdf", as_attachment=True, download_name=fname)


def _wrap_text(text, width):
    words = text.split(" ")
    lines, cur = [], ""
    for w in words:
        if len(cur) + len(w) + 1 <= width:
            cur = (cur + " " + w).strip()
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


@app.route("/biodata/<int:profile_id>/png")
@login_required
def biodata_png(profile_id):
    from PIL import Image, ImageDraw, ImageFont

    db = get_db()
    row = db.execute("SELECT * FROM profiles WHERE id = ?", (profile_id,)).fetchone()
    if not row:
        abort(404)
    profile = attach_photos(db, row_to_dict(row))

    W, H = 1000, 1400
    img = Image.new("RGB", (W, H), "#fbf8f1")
    draw = ImageDraw.Draw(img)

    def font(size, bold=False):
        try:
            path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold \
                else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
            return ImageFont.truetype(path, size)
        except Exception:
            return ImageFont.load_default()

    maroon = (139, 30, 63)
    indigo = (27, 58, 99)
    gold = (201, 151, 43)
    ink = (20, 22, 31)

    draw.rectangle([0, 0, W, 70], fill=maroon)
    draw.text((30, 20), "Sindhi Samaj Pariwar Surat — Marriage Biodata", font=font(26, True), fill="white")

    y = 100
    photo_path = None
    if profile["photos"]:
        photo_path = os.path.join(UPLOAD_DIR, profile["photos"][0].split("/uploads/")[-1])
    if photo_path and os.path.exists(photo_path):
        try:
            ph = Image.open(photo_path).convert("RGB")
            ph.thumbnail((260, 320))
            img.paste(ph, (W - 300, y))
        except Exception:
            pass

    draw.text((30, y), profile.get("full_name") or "Unnamed Profile", font=font(34, True), fill=indigo)
    y += 55

    for section_title, rows in biodata_lines(profile):
        draw.text((30, y), section_title, font=font(20, True), fill=gold)
        y += 28
        draw.line([(30, y), (W - 320 if y < 420 else W - 30, y)], fill=gold, width=2)
        y += 12
        for label, val in rows:
            text = f"{label}: {val}"
            draw.text((40, y), text[:110], font=font(16), fill=ink)
            y += 26
        y += 14

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    fname = f"biodata_{secure_filename(profile.get('full_name') or str(profile_id))}.png"
    return send_file(buf, mimetype="image/png", as_attachment=True, download_name=fname)


# ---------------------------------------------------------------------------
# Stats (for admin dashboard)
# ---------------------------------------------------------------------------
@app.route("/api/stats")
@login_required
def api_stats():
    db = get_db()
    total = db.execute("SELECT COUNT(*) FROM profiles").fetchone()[0]
    brides = db.execute("SELECT COUNT(*) FROM profiles WHERE profile_for = 'Bride'").fetchone()[0]
    grooms = db.execute("SELECT COUNT(*) FROM profiles WHERE profile_for = 'Groom'").fetchone()[0]
    active = db.execute("SELECT COUNT(*) FROM profiles WHERE status = 'Active'").fetchone()[0]
    return jsonify({"success": True, "total": total, "brides": brides, "grooms": grooms, "active": active})


init_db()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
