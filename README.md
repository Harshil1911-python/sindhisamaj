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
| `view.html` | **Main feature** — walk-in "View Profiles" screen: filter drawer + 3-column photo cards + detail modal + QR + biodata download + approve/reject + compare + kundli viewer + suggested matches |
| `login.html` | Login page for registrants (separate from admin `signin.html`) — uses email/phone + the password set at registration |
| `dashboard.html` | Self-service dashboard where a registrant can view/edit their own profile, manage photos, and change password |
| `matches.html` | Review and manage shortlisted profile pairs (Proposed / Accepted / Declined) |
| `reports.html` | Analytics dashboard — registration trends, gender/status/age/city/caste breakdowns |
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

### Security & polish
- **Login rate-limiting**: 5 failed sign-in attempts (per username or per IP)
  locks further attempts for 15 minutes. This is enforced server-side, so
  it can't be bypassed from the browser.
- **Server-side validation** on registration: phone numbers must be valid
  10-digit Indian mobile numbers, email must be a valid format — checked
  both in the browser (`pattern` attributes) and again on the server.

### Workflow & trust
- **Approval queue**: every new self-registration is saved with status
  `Pending` and is **hidden from Walk-in View by default**. The Dashboard
  shows a "Pending Approvals" panel where you can Approve (→ `Active`) or
  Reject (→ `Rejected`) each one. You can still see Pending/Rejected
  profiles in `view.html` by explicitly selecting that status in the
  filters.
- **Admin Notes**: a private notes field on every profile (visible only in
  the admin detail/edit view) for things like "met on 5 July, interested in
  Ahmedabad matches" — never shown on the public QR/details page or in CSV
  export.

### Matching
- **Compare Mode**: toggle it on in `view.html`, tick two profile cards,
  and click "Compare Selected" for a side-by-side field comparison (with
  differences bolded) — with a one-click "Shortlist This Pair" button.
- **Suggest Matches**: inside a profile's detail modal, click "Suggest
  Matches" to see a ranked list of opposite-gender active profiles, scored
  by age closeness, same caste, same city, same marital status, and same
  manglik status — shortlist any of them directly from the suggestion card.
- **Matches page** (`matches.html`): review every shortlisted pair, filter
  by Proposed / Accepted / Declined, update status, or remove a match.

### Kundli PDF viewer
- If a profile uploaded a Kundli PDF during registration, the "View Kundli
  PDF" button in the detail modal opens it **inline** in an embedded viewer
  (no download needed) — browsers render PDFs natively inside the `iframe`.

### Data & Reporting (`reports.html`)
- Registrations-over-time trend line, **Male vs Female split** (by `gender`, not registering-as Bride/Groom), status
  breakdown, age distribution, marital status breakdown, top cities, and
  top Sindhi castes — all pulled live from `/api/reports` and charted with
  Chart.js (loaded from CDN).

### Horoscope compatibility (approximate)
- In Compare Mode, the comparison view now shows a simplified Ashtakoot-style
  compatibility score covering 4 of the 8 traditional factors (Varna, Gana,
  Nadi, Bhakoot) plus a Manglik check, computed from each profile's Rashi
  and Nakshatra fields. **This is explicitly labeled as an approximate
  screening aid** — the UI always shows a disclaimer recommending a full
  36-guna reading from a qualified astrologer/pandit before finalizing any
  match. If Rashi/Nakshatra spelling can't be recognized, it says so rather
  than guessing.

### Registrant self-service dashboard
- Registration now **requires** a password (previously optional), since it's
  used to log in later.
- `login.html` — registrants log in with the email or phone + password they
  set at registration (separate from the admin login, completely separate
  session).
- `dashboard.html` — registrants can see their own profile, a **completeness
  %** bar, edit any of their details, manage their photo gallery (add,
  delete, set main photo, **drag to reorder**), and change their password.
  **Any self-edit sends the profile back to `Pending` for bureau
  re-approval** before it's visible in Walk-in View again.
- The same drag-to-reorder gallery UI was also added to the admin's Edit
  Profile screen in `view.html`.

### Excel export & import
- Alongside CSV, the Dashboard now also offers **Export as Excel (.xlsx)**
  (styled header row, auto-sized columns) and **Import from Excel**, using
  the same field set as `register.html`.

### Save & resume registration
- `register.html` now auto-saves your progress (text/select/date fields) to
  the browser's local storage as you type. If you leave and come back, a
  banner offers to **Resume** or **Discard** the draft. Uploaded photos
  can't be restored this way (browser security) and need re-selecting.

### QR download
- The QR code shown in a profile's detail modal now has a **Download QR**
  button, saving it as `profile_<id>_qr.png`.



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
  (multiple file upload) since the admin card/QR view needs profile photos,
  plus a **Reference** section for "filled on behalf of" cases. Password is
  now **required** at registration, since it powers the registrant's own
  login (see below).
- Verification documents (Aadhar, passport — both numbers and photos) are
  visible to admins only in `view.html`, and are always excluded from the
  public QR/details view. The Reference fields and Admin Notes are excluded
  from the public view for the same reason.
- Passwords set at registration now power the registrant's own login —
  same unified `signin.html` page as admins use, but a completely separate
  session, so a registrant can never reach `admin.html` or `view.html`
  with their own credentials.

### Bug fix: filters / bulk import
- **Found and fixed the cause of "filters not working."** CSV/Excel imports
  were silently landing with status `Pending` (the same default used for
  public self-registrations), so bulk-imported profiles never appeared in
  Walk-in View — no matter what filter was applied — until each one was
  individually approved. Admin-driven CSV/Excel imports now insert as
  `Active` immediately, since that data is already trusted/vetted by the
  office. (Public self-registration still correctly defaults to `Pending`.)
  Every filter (single, combined, age range, birth year range, search) was
  re-tested against realistic bulk-imported data and works correctly.

### Reference field
- `register.html` now has a **Reference** section: "Filling this form on
  behalf of someone? Enter their name" plus a **Relation to Candidate**
  dropdown (Father/Mother/Sibling/Relative/Friend/Bureau Staff/Other) —
  for cases where a parent or relative is registering on someone's behalf.
- Included in CSV/Excel export and import, editable by admins in
  `view.html` and by the registrant in `dashboard.html`, but **always
  excluded from the public QR/details page** (internal bureau info only).

### Unified login
- `signin.html` is now a single **Login** page for everyone. The backend
  tries the entered username as an admin login first, then falls back to
  checking it as a registrant's email/phone — whichever matches sends you
  to the right place (`admin.html` or `dashboard.html`). The old
  `login.html` still works as a redirect to `signin.html` for anyone with
  it bookmarked. The landing page now just shows one "Login" button.

### Reports/stats: Male vs Female
- Both `reports.html` and the admin Dashboard stat cards now show **Male /
  Female** counts (based on the `gender` field) instead of Bride/Groom
  counts (which reflected what someone registered *as*, not their gender).

### Easier Kundli management
- The Kundli PDF is no longer locked to whatever was uploaded at
  registration time. A shared upload endpoint now lets **admins** (from
  `view.html`) and **registrants themselves** (from `dashboard.html`)
  upload, replace, or remove a Kundli PDF at any time — with clear
  before/after states (an empty-state message if none exists yet, an
  inline PDF viewer plus "Open in New Tab" and "Remove" once one is
  uploaded). The "View Kundli PDF" button is now always clickable instead
  of being grayed out when nothing was uploaded yet.

### Admin can reset a member's password
- Inside a profile's detail modal in `view.html`, click **"Set User
  Password"** to set a new login password for that registrant directly —
  no need to know their current one. Useful when a member forgets their
  password or needs their `dashboard.html` login set up for them at the
  office. Enforces the same 6-character minimum as everywhere else.

### Bug fix: deleted profiles "reappearing"
- **Found and fixed the cause.** `/api/` responses had no cache-control
  headers, so a browser (or any proxy in between) could serve a stale
  cached copy of `/api/profiles` after a delete, making it look like the
  deleted profile "came back after some time." Every `/api/` response now
  sends `Cache-Control: no-store` (plus matching `Pragma`/`Expires`
  headers), and the main list-loading fetches in `view.html`, `admin.html`,
  and `matches.html` also explicitly request `cache: 'no-store'`. Deletes
  were re-verified to properly cascade-remove a profile's photos and any
  matches it was part of, and repeated polling after a delete confirmed
  the profile never reappears.

### Fields removed
- `register.html` no longer collects **Rashi, Nakshatra, Mulank, or Birth
  Chart Details**, and the entire **Verification Documents** section
  (Aadhar number/photo, Passport number/photo) has been removed.
- These fields are gone from CSV export/import, Excel export/import, the
  admin edit screen (`view.html`), the registrant dashboard
  (`dashboard.html`), and the public details page — consistently, in one
  place (`PROFILE_FIELDS` in `app.py`), so every format stays in sync.
- Manglik, Kundli (available + PDF upload), and Horoscope Notes are all
  still collected — only Rashi/Nakshatra/Mulank/Birth Chart were removed.
- The horoscope compatibility check in Compare Mode now always shows the
  **Manglik comparison** (which doesn't depend on the removed fields), and
  gracefully explains that the fuller Ashtakoot score isn't available since
  Rashi/Nakshatra are no longer collected (it still works automatically for
  any old profiles that already have that data saved).
- `landing.html` has been replaced with your own updated version (the
  image-carousel design) — nothing in the backend depends on its internals
  beyond the links to `register.html` and `signin.html`, which are unchanged.

### Manglik Status: radio buttons instead of a dropdown
- `register.html`'s Manglik Status field is now a **radio button group**
  (Yes / No / Partial / Not Sure) instead of a select dropdown, matching
  the style you wanted (no "drawer"/dropdown for this field).
- Added a **"Not Sure"** option that wasn't there before.
- Fixed a latent bug this exposed: the Save & Resume draft feature
  (`register.html`'s auto-save-to-browser-storage) was written assuming
  every field was a plain text/select input. It would have mis-saved and
  mis-restored radio button groups (grabbing whichever radio happened to
  be last in the DOM, and not actually re-selecting the right one on
  resume). Both the save and resume logic now correctly handle radio
  (and checkbox) inputs.
- "Not Sure" was added everywhere Manglik shows up as a dropdown for
  consistency: the admin edit screen (`view.html`), the registrant
  dashboard (`dashboard.html`), and the Manglik filter in Walk-in View.
- The horoscope compatibility check now treats **"Not Sure" as
  indeterminate** rather than assuming compatibility — if either profile's
  Manglik status is "Not Sure," the result explains it can't be determined
  instead of guessing.
- `landing.html` updated again to your latest version (new address, "Free"
  branding, Hindi title) — same as before, it only links to
  `register.html`/`signin.html` so nothing else needed to change.

### Bulk Actions (delete, approve, reject)
- `view.html` now has a **"Bulk Actions"** toggle next to Compare Mode.
  Turning it on shows a checkbox on every card — select as many profiles
  as you like (or click "Select All Visible" to grab everyone currently
  filtered into view), then **Approve**, **Reject**, or **Delete** all of
  them in one action, each with a confirmation prompt. Compare Mode and
  Bulk Actions are mutually exclusive — turning one on switches the other
  off automatically, so there's no confusion about what a click on a card
  does.
- Backed by a new `POST /api/profiles/bulk-action` endpoint that applies
  the action to a whole list of profile IDs in one transaction.

### Birth Year filter, made easier to find
- Added a plain **"Birth Year"** dropdown (populated with the actual years
  present in your data) right next to the existing birth-year *range*
  filter — so "show me everyone born in 1990" is now a single dropdown
  pick instead of typing the same year into both the "from" and "to" range
  boxes. Both options remain available depending on whether you want an
  exact year or a range.

### Bug fix: backup/restore now includes photos and Kundli PDFs
- **Found the cause.** Backup only ever downloaded the raw `database.db`
  file — it never included anything in `uploads/` (profile photos, Kundli
  PDFs), so restoring brought back all the profile data but every photo
  link pointed at a file that no longer existed.
- Backup now downloads a single **`.zip`** file containing `database.db`
  plus every file in `uploads/`. Restore accepts that `.zip` and puts both
  back exactly as they were — re-tested end-to-end with real image and PDF
  files to confirm they survive a full backup → wipe → restore cycle.
- Old database-only `.db`/`.sqlite`/`.sqlite3` backups from before this fix
  still work for restore (for backward compatibility) — you'll just get a
  note that no images came back with it, since there weren't any in that
  older backup format to begin with.

