import os

# Base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Flask configuration
SECRET_KEY = 'grs-2026-secure-key-change-in-production'
DEBUG = True

# Database configuration
DATABASE_PATH = os.path.join(BASE_DIR, 'database', 'grievances.db')

# Upload configuration
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

# Complaint Categories
CATEGORIES = [
    'Water Supply',
    'Electricity',
    'Road Maintenance',
    'Sanitation',
    'Salary Issue',
    'Infrastructure',
    'Public Safety',
    'Other'
]

# Department Mapping
DEPARTMENT_MAPPING = {
    'Water Supply':     'Public Works Department',
    'Electricity':      'Electrical Department',
    'Road Maintenance': 'Public Works Department',
    'Sanitation':       'Sanitation Department',
    'Salary Issue':     'Human Resources Department',
    'Infrastructure':   'Municipal Corporation',
    'Public Safety':    'Police Department',
    'Other':            'General Administration'
}

# ── HIGH Priority Keywords (expanded — weapons/terror/violence) ──
HIGH_PRIORITY_KEYWORDS = [
    # ── WEAPONS / EXPLOSIVES / NATIONAL SECURITY ──────────────────
    'bomb', 'bombs', 'bombing', 'explosive', 'explosives',
    'weapon', 'weapons', 'arms', 'ammunition', 'grenade', 'ied',
    'gun', 'pistol', 'rifle', 'firearm', 'firearms',
    'terror', 'terrorist', 'terrorism', 'extremist', 'militant', 'insurgent',
    'make bomb', 'making bomb', 'collecting weapons', 'collecting arms',

    # ── VIOLENCE / HARM TO PEOPLE ─────────────────────────────────
    'kill', 'killing', 'killed', 'murder', 'murderer',
    'hurt people', 'hurt person', 'hurt civilians',
    'attack people', 'attacking people',
    'rape', 'sexual assault', 'molestation',
    'kidnap', 'kidnapped', 'abduction',
    'mob violence', 'riot', 'rioting', 'communal violence',

    # ── FIRE / COLLAPSE / ELECTROCUTION ───────────────────────────
    'fire', 'arson', 'burning', 'ablaze',
    'collapse', 'roof collapsed', 'building collapsed',
    'electric shock', 'electrocution', 'electrocuted',

    # ── MEDICAL EMERGENCY / DEATH ─────────────────────────────────
    'dead', 'death', 'died', 'dying', 'fatal',
    'injury', 'injured', 'bleeding', 'unconscious',

    # ── SERVICE COMPLETELY STOPPED ────────────────────────────────
    'no water', 'no electricity', 'no power', 'no light',
    'completely stopped', 'total failure', 'total outage', 'blackout',

    # ── EXPLICIT URGENCY ──────────────────────────────────────────
    'urgent', 'emergency', 'critical', 'immediate', 'severe',
    'life threatening', 'life-threatening', 'sos',
    'contaminated', 'toxic', 'poisoned',
    'dangerous', 'hazard', 'extremely dangerous',
]

# ── MEDIUM Priority Keywords ──────────────────────────────────────
MEDIUM_PRIORITY_KEYWORDS = [
    'problem', 'issue', 'delay', 'pending', 'broken', 'damaged',
    'intermittent', 'irregular', 'low pressure', 'dim light', 'fluctuation',
    'pothole', 'repair needed', 'maintenance required', 'complaint',
    'facing problem', 'inconvenience', 'not working properly', 'defective',
    'stray dog', 'noise', 'encroachment', 'garbage overflow',
]

# Resolution Timeline
RESOLUTION_TIMELINE = {
    'High':   '24–48 hours',
    'Medium': '3–7 days',
    'Low':    '7–14 days'
}

# Admin Credentials
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'admin123'

# Model Configuration
TROCR_MODEL      = 'microsoft/trocr-base-handwritten'
DISTILBERT_MODEL = 'typeform/distilbert-base-uncased-mnli'
