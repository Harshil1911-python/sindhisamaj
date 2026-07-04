-- Sindhi Samaj Pariwar Surat -- Marriage Bureau Database Schema

CREATE TABLE IF NOT EXISTS admins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    public_token TEXT UNIQUE,
    status TEXT DEFAULT 'Pending',             -- Pending / Active / Inactive / Matched / Hold / Rejected
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),

    -- Basic Information
    full_name TEXT,
    gender TEXT,
    profile_for TEXT,
    father_name TEXT,
    mother_name TEXT,
    guardian_name TEXT,
    dob TEXT,
    time_of_birth TEXT,
    place_of_birth TEXT,
    age INTEGER,
    height TEXT,
    weight TEXT,
    blood_group TEXT,
    complexion TEXT,
    body_type TEXT,
    nationality TEXT,
    religion TEXT,
    community TEXT,
    sindhi_caste TEXT,
    sub_caste TEXT,
    mother_tongue TEXT,

    -- Marital Status
    marital_status TEXT,
    children TEXT,

    -- Occupation & Career
    occupation TEXT,
    career TEXT,
    company TEXT,
    business TEXT,
    designation TEXT,
    income_monthly TEXT,
    income_yearly TEXT,

    -- Education
    qualification TEXT,
    college TEXT,
    university TEXT,

    -- Address & Contact
    current_city TEXT,
    native_place TEXT,
    phone TEXT,
    alternate_phone TEXT,
    email TEXT,
    whatsapp TEXT,
    emergency_contact TEXT,
    permanent_address TEXT,
    temporary_address TEXT,

    -- Lifestyle
    food_preference TEXT,
    smoking TEXT,
    drinking TEXT,
    habits TEXT,
    hobbies TEXT,
    interests TEXT,
    languages_known TEXT,
    about_yourself TEXT,

    -- Partner Preference
    expected_age TEXT,
    expected_height TEXT,
    expected_education TEXT,
    expected_profession TEXT,
    expected_income TEXT,
    expected_location TEXT,
    expected_lifestyle TEXT,

    -- Astrological Details
    manglik TEXT,
    rashi TEXT,
    nakshatra TEXT,
    mulank TEXT,
    kundli_available TEXT,
    kundli_pdf_path TEXT,
    birth_chart TEXT,
    horoscope_notes TEXT,

    -- Medical
    disability TEXT,
    special_notes TEXT,

    -- Verification
    aadhar_number TEXT,
    aadhar_photo_path TEXT,
    passport_number TEXT,
    passport_photo_path TEXT,

    -- Account
    password_hash TEXT,

    -- Admin-only
    admin_notes TEXT
);

CREATE TABLE IF NOT EXISTS photos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id INTEGER NOT NULL,
    filepath TEXT NOT NULL,
    is_primary INTEGER DEFAULT 0,
    sort_order INTEGER DEFAULT 0,
    FOREIGN KEY (profile_id) REFERENCES profiles(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS matches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_a_id INTEGER NOT NULL,
    profile_b_id INTEGER NOT NULL,
    status TEXT DEFAULT 'Proposed',            -- Proposed / Accepted / Declined
    notes TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (profile_a_id) REFERENCES profiles(id) ON DELETE CASCADE,
    FOREIGN KEY (profile_b_id) REFERENCES profiles(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS login_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    ip TEXT,
    success INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_photos_profile ON photos(profile_id);
CREATE INDEX IF NOT EXISTS idx_profiles_gender ON profiles(gender);
CREATE INDEX IF NOT EXISTS idx_profiles_city ON profiles(current_city);
CREATE INDEX IF NOT EXISTS idx_profiles_caste ON profiles(sindhi_caste);
CREATE INDEX IF NOT EXISTS idx_matches_a ON matches(profile_a_id);
CREATE INDEX IF NOT EXISTS idx_matches_b ON matches(profile_b_id);
CREATE INDEX IF NOT EXISTS idx_login_attempts_lookup ON login_attempts(username, ip, created_at);
