# Sindhi Samaj Pariwar Surat — Marriage Bureau Software

A self-contained Flask + SQLite marriage bureau system. All source files sit
loose in one folder (no subfolders) as requested — `uploads/` is just a
runtime folder the app creates on its own to store photos/documents.

## Files

| File | Purpose |
|---|---|
| `landing.html` | Public homepage (uses `bg.png` as background) |
| `register.html` | Public registration form (all biodata fields + photos) |
| `signin.html` | Admin sign-in |
| `admin.html` | Admin dashboard — stats, CSV import/export, backup/restore, admin management |
| `view.html` | **Main feature** — walk-in "View Profiles" screen: filter drawer + 3-column photo cards + detail modal + QR + biodata download |
| `details.html` | Public, read-only profile page (this is where the QR code on each profile points — no admin functions) |
| `app.py` | Flask backend (all routes, DB access, CSV, PDF/PNG biodata generation, QR generation) |
| `schema.sql` | SQLite schema |
| `requirements.txt` | Python dependencies |
| `Procfile` / `render.yaml` | Deployment config for Render |
| `bg.png` | Desktop hero background — **replace with a real photo/graphic**, same filename |
| `bgmob.png` | Mobile hero background (shown instead of `bg.png` on phones) — replace with a portrait-oriented image, same filename |

## Running locally

```bash
pip install -r requirements.txt
python app.py
```

Visit `http://localhost:5000`. On first run the app creates `database.db`
and prints a default admin login:

```
username: admin
password: admin123
```

**Sign in and change this password immediately** (Dashboard → Change My
Password).

## How it works

- **Anyone** can open `register.html` and submit their biodata + photos —
  no login required to register.
- **Only admins** can sign in (`signin.html`) and reach `admin.html` / `view.html`.
- From the Dashboard, click **"View Profiles (Walk-in Mode)"** to open
  `view.html`: this is meant to be used with a walk-in bride/groom sitting
  with the admin. The left drawer has collapsible filter groups for every
  field (gender, city, caste, education, lifestyle, astrological details,
  age range, etc.) — click the gold `☰` tab to collapse/expand the whole
  drawer. The right side shows photo cards, 3 per row. Clicking a card opens
  a full detail view with an enlargeable photo gallery, every field the
  person filled in, a **QR code**, and one-click **Biodata PDF / PNG**
  downloads generated on the fly from the profile data.
- The **QR code** on each profile links to `details.html?token=...` — a
  public, read-only page with no admin controls and no verification
  documents (Aadhar/passport photos and numbers are always stripped from
  this view — only visible to admins in `view.html`).
- Each profile can have **multiple photos** — uploaded together during
  registration (first one becomes the main display photo), and admins can
  add more, delete individual ones, or change which one is the "main"
  photo from the **Edit Profile** screen in `view.html`.
- **Edit Profile**: inside the detail modal in `view.html`, click "Edit
  Profile" to turn every field into an editable input (with dropdowns for
  fields like gender, marital status, manglik, status, etc.), replace the
  photo, and save — updates are written straight to the database.
- **Filters** now include a **Birth Year range** (in addition to Age range)
  so you can search by year of birth directly.
- The **landing page background** automatically switches between `bg.png`
  (desktop/tablet) and `bgmob.png` (phones), detected via screen width and
  user agent — replace both files with your own artwork, keeping the same
  filenames.
- **CSV Export/Import** on the Dashboard uses the exact field set from
  `register.html`, so a spreadsheet edited externally can be re-imported.
- **Backup/Restore** downloads or replaces the raw SQLite `database.db`
  file.

## Deploying to Render

1. Push this folder to a GitHub repo.
2. On Render: New → Blueprint → point at the repo (it will read `render.yaml`),
   or New → Web Service with:
   - Build command: `pip install -r requirements.txt`
   - Start command: `gunicorn app:app --bind 0.0.0.0:$PORT`
3. **Persistence note:** SQLite + uploaded photos are just files on disk.
   Render's **free** plan has an ephemeral filesystem — everything resets on
   every deploy/restart. `render.yaml` is set up to attach a persistent disk
   at `/var/data` (via the `DATA_DIR` env var), but persistent disks require
   a **paid** Render instance type. On the free plan, either accept that data
   resets on redeploy, or move to a paid plan / external storage.
4. Set the `SECRET_KEY` env var to something random in production
   (`render.yaml` already auto-generates one for you).

## Notes

- `register.html` was extended from your example with a **Photos** section
  (multiple file upload) since the admin card/QR view needs profile photos.
  Password is now optional (members don't log in — only admins do).
- Verification documents (Aadhar, passport — both numbers and photos) are
  visible to admins only in `view.html`, and are always excluded from the
  public QR/details view.
