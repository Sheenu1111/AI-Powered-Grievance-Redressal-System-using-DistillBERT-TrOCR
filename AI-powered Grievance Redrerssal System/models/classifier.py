"""
DistilBERT-based Complaint Classifier — v2.1 (Priority Engine Hotfix)

ROOT CAUSE FIX:
  - "bomb", "weapon", "hurt people", "kill", "terror" were MISSING from all patterns
  - Category engine missing weapon/bomb/terror → fell to "Other" → "General Administration"
  - Priority engine ran before category engine → Public Safety boost never triggered

EXECUTION ORDER (now fixed):
  1. Detect category FIRST (so Public Safety boost works correctly)
  2. Run Critical HIGH instant-override patterns (vastly expanded)
  3. Run contextual rules
  4. Apply category-specific boosts
  5. Keyword fallback
"""

import re
from config import CATEGORIES, HIGH_PRIORITY_KEYWORDS, MEDIUM_PRIORITY_KEYWORDS


# ══════════════════════════════════════════════════════════════
# CRITICAL HIGH — Instant override. Any match → HIGH priority.
# Order matters: most severe checks are at the top.
# ══════════════════════════════════════════════════════════════

INSTANT_HIGH_PATTERNS = [

    # ── 🔴 WEAPONS / TERRORISM / NATIONAL SECURITY (NEW) ──────────
    r'\b(bomb|bombs|bombing|explosive|explosives|ied|landmine)\b',
    r'\b(weapon|weapons|arms|ammunition|ammo|grenade|grenade)\b',
    r'\b(gun|guns|pistol|rifle|firearm|firearms|knifepoint|knife.?attack)\b',
    r'\b(terror|terrorist|terrorism|extremist|militant|insurgent|jihadist)\b',
    r'\b(blast|explosion|detonat|blew.?up)\b',
    r'\b(kill|killing|killed|murder|murderer|massacre|genocide)\b',
    r'\bhurt\s+(people|person|someone|anyone|others|civilians)\b',
    r'\b(attack|attacked|attacking).{0,25}(people|civilians|village|area|school|market)\b',
    r'\b(making|collecting|assembling|preparing).{0,30}(bomb|weapon|explosive|arms)\b',
    r'\b(suspicious.{0,20}(collect|gather|material|stuff|thing))\b',
    r'\b(material.{0,20}(bomb|weapon|explosive))\b',

    # ── 🔴 FIRE / STRUCTURAL COLLAPSE ─────────────────────────────
    r'\b(fire|arson|burning|ablaze|inferno)\b',
    r'\b(collapse|collapsed|building.?fell|roof.?fell|wall.?fell)\b',
    r'\b(electric.?shock|electrocution|electrocuted|sparking.?wire)\b',

    # ── 🔴 MEDICAL EMERGENCY / DEATH ──────────────────────────────
    r'\b(dead|death|died|dying|fatality|fatalities)\b',
    r'\b(injury|injured|injuries|bleeding|unconscious|critical.?condition)\b',
    r'\b(ambulance|hospital.{0,15}emergency|medical.?emergency)\b',
    r'\b(contaminated.{0,15}water|toxic|poison|poisoned|sewage.{0,10}drin)\b',
    r'\b(disease.{0,15}spread|epidemic|outbreak|infection.{0,15}spreading)\b',

    # ── 🔴 VIOLENCE / CRIME IN PROGRESS ──────────────────────────
    r'\b(rape|sexual.?assault|molestation|kidnap|kidnapped|abduction)\b',
    r'\b(robbery|armed.?robbery|dacoity|dacoit)\b',
    r'\b(mob|rioting|riot|lynching|communal.?violence)\b',

    # ── 🔴 UTILITIES COMPLETELY STOPPED ───────────────────────────
    r'\bno\s+(water|electricity|power|light|supply)\b',
    r'\b(water|electricity|power).{0,20}(completely|totally).{0,15}(stopped|cut|gone|failed)\b',
    r'\b(total|complete|absolute).{0,15}(outage|failure|blackout|shutdown)\b',

    # ── 🔴 FLOOD / NATURAL DISASTER ───────────────────────────────
    r'\b(flood|flooding|flooded|submerged|waterlogging.{0,15}severe)\b',
    r'\b(earthquake|landslide|cyclone|storm.{0,10}destroy)\b',

    # ── 🔴 EXPLICIT URGENCY KEYWORDS ──────────────────────────────
    r'\b(emergency|life.?threat|sos|help.?immediately|urgent.?action)\b',
    r'\b(immediate(ly)?|critical(ly)?|extremely.{0,10}dangerous)\b',
]

# ══════════════════════════════════════════════════════════════
# CONTEXTUAL HIGH — Check value from captured group
# ══════════════════════════════════════════════════════════════

CONTEXTUAL_HIGH_RULES = [
    # Duration: 7+ days = High
    (r'(\d+)\s*\+?\s*(days?)',    lambda m: int(m.group(1)) >= 7),
    # Duration: any weeks/months
    (r'(\d+)\s*(weeks?|months?)', lambda m: True),
    # Entire area/community affected
    (r'\b(entire|whole|all|full)\s+\w*\s*(area|colony|village|sector|block|ward|society|community|district|town|city)\b',
     lambda m: True),
    # Large number of people
    (r'\b(\d+)\s*(families|households|residents|people|persons|citizens)\b',
     lambda m: int(m.group(1)) >= 50),
    # Corruption with funds
    (r'\b(bribe|corruption|embezzlement|fraud|misuse).{0,25}(fund|crore|lakh|money|public)\b',
     lambda m: True),
    # No response for long time
    (r'\b(no\s+response|no\s+action).{0,25}(days?|weeks?|months?)\b',
     lambda m: True),
]

# ══════════════════════════════════════════════════════════════
# CONTEXTUAL MEDIUM
# ══════════════════════════════════════════════════════════════

CONTEXTUAL_MEDIUM_RULES = [
    (r'(\d+)\s*(days?)', lambda m: int(m.group(1)) >= 3),
    (r'\b(damaged|broken|not.?working|defective|irregular).{0,20}(road|pipe|wire|transformer|pump|motor)\b',
     lambda m: True),
    (r'\b(pothole|crack|leakage|low.?pressure|fluctuation)\b', lambda m: True),
]


# ══════════════════════════════════════════════════════════════
# CATEGORIES that are inherently HIGH or MEDIUM regardless
# ══════════════════════════════════════════════════════════════

CATEGORY_PRIORITY_FLOOR = {
    'Public Safety': 'High',      # Any public safety issue → High
    'Salary Issue':  'Medium',    # Any salary issue → at least Medium
}


class ComplaintClassifier:
    """
    Complaint classifier using:
      1. DistilBERT zero-shot (if available)  → Category
      2. Keyword scoring fallback             → Category
      3. Multi-factor pattern engine          → Priority
    """

    def __init__(self):
        self.distilbert_available = False
        self.classifier_pipeline = None

        # Avoid downloading the zero-shot model during app startup. We keep the
        # keyword engine available immediately and load DistilBERT on demand.
        self.category_keywords = {
            'Water Supply': [
                'water', 'tap', 'pipeline', 'leakage', 'shortage', 'drinking water',
                'contaminated water', 'water supply', 'muddy water', 'water tank',
                'borewell', 'handpump', 'tube well', 'jal board', 'no water',
                'water cut', 'water disrupted'
            ],
            'Electricity': [
                'electricity', 'power', 'light', 'electric', 'blackout', 'voltage',
                'transformer', 'power cut', 'electric pole', 'wire', 'meter', 'bill',
                'load shedding', 'outage', 'sparking', 'short circuit', 'no power',
                'power failure', 'power disruption'
            ],
            'Road Maintenance': [
                'road', 'pothole', 'street', 'highway', 'pavement', 'footpath',
                'divider', 'speed breaker', 'broken road', 'pit', 'mud on road',
                'waterlogged road', 'road damage', 'road repair'
            ],
            'Sanitation': [
                'garbage', 'waste', 'trash', 'sewage', 'drain', 'cleaning',
                'dustbin', 'sanitation', 'dirty', 'filth', 'stink', 'smell',
                'sewage overflow', 'toilet', 'open defecation', 'manhole',
                'sweeper', 'cleanliness', 'dumping', 'litter', 'nali'
            ],
            'Salary Issue': [
                'salary', 'payment', 'wage', 'paycheck', 'compensation', 'pay',
                'arrears', 'pending payment', 'dues', 'emolument', 'stipend',
                'not paid', 'salary not', 'increment', 'bonus', 'allowance',
                'salary pending', 'salary withheld'
            ],
            'Infrastructure': [
                'building', 'construction', 'infrastructure', 'facility', 'structure',
                'maintenance', 'park', 'school building', 'hospital building',
                'community center', 'government building', 'encroachment',
                'boundary wall', 'street light', 'footpath repair'
            ],
            'Public Safety': [
                # Original
                'safety', 'crime', 'theft', 'violence', 'police', 'security',
                'danger', 'threat', 'robbery', 'assault', 'harassment', 'molestation',
                'eve teasing', 'chain snatching', 'burglary', 'suspicious', 'cctv',
                # NEW — weapons, terror, harm
                'bomb', 'bombs', 'bombing', 'explosive', 'weapon', 'weapons',
                'arms', 'ammunition', 'gun', 'pistol', 'rifle', 'firearm',
                'terror', 'terrorist', 'terrorism', 'extremist', 'militant',
                'insurgent', 'kill', 'killing', 'murder', 'attack', 'hurt',
                'injure', 'kidnap', 'abduction', 'rape', 'sexual assault',
                'rioting', 'riot', 'mob violence', 'communal', 'grenade',
                'ied', 'blast', 'detonation', 'suspicious activity',
                'collecting material', 'make bomb', 'making bomb',
                # Location-sensitive
                'srinagar', 'kashmir', 'border area', 'militant area'
            ],
            'Other': []
        }

    def _load_distilbert(self):
        """Load DistilBERT zero-shot classification pipeline on demand."""
        if self.classifier_pipeline is not None:
            return True

        try:
            print("Loading DistilBERT zero-shot classifier...")
            from transformers import pipeline
            self.classifier_pipeline = pipeline(
                "zero-shot-classification",
                model="typeform/distilbert-base-uncased-mnli",
                device=-1
            )
            self.distilbert_available = True
            print("DistilBERT classifier loaded successfully!")
            return True
        except Exception as e:
            print(f"DistilBERT not loaded ({e}). Using keyword fallback.")
            self.classifier_pipeline = None
            self.distilbert_available = False
            return False

    # ─────────────────────────────────────────────────────────────
    # CATEGORY DETECTION
    # ─────────────────────────────────────────────────────────────

    def classify_category_distilbert(self, text):
        """Zero-shot DistilBERT classification"""
        try:
            candidate_labels = [
                "water supply problem",
                "electricity and power problem",
                "road and street maintenance",
                "garbage and sanitation problem",
                "salary and payment issue",
                "infrastructure and building problem",
                "public safety, crime, weapons, or national security threat",
                "other general complaint"
            ]
            label_to_category = {
                "water supply problem":                               "Water Supply",
                "electricity and power problem":                     "Electricity",
                "road and street maintenance":                        "Road Maintenance",
                "garbage and sanitation problem":                    "Sanitation",
                "salary and payment issue":                          "Salary Issue",
                "infrastructure and building problem":               "Infrastructure",
                "public safety, crime, weapons, or national security threat": "Public Safety",
                "other general complaint":                           "Other"
            }
            result    = self.classifier_pipeline(text, candidate_labels)
            top_label = result['labels'][0]
            confidence = result['scores'][0]

            if confidence < 0.22:
                return None
            return label_to_category.get(top_label, 'Other')

        except Exception as e:
            print(f"DistilBERT inference error: {e}")
            return None

    def classify_category_keywords(self, text):
        """
        Keyword scoring fallback.
        Uses weighted scoring — longer/more specific keywords score higher.
        """
        text_lower = text.lower()
        scores = {}

        for category, keywords in self.category_keywords.items():
            score = 0
            for kw in keywords:
                if kw in text_lower:
                    # Longer keywords = more specific = higher weight
                    weight = len(kw.split())
                    score += weight * text_lower.count(kw)
            scores[category] = score

        # ── Hard override: if ANY weapon/bomb/terror keyword is present,
        #    force Public Safety regardless of score ──────────────────
        security_terms = [
            'bomb', 'weapon', 'explosive', 'terror', 'terrorist',
            'kill', 'murder', 'gun', 'pistol', 'rifle', 'grenade',
            'militant', 'insurgent', 'extremist', 'hurt people',
            'hurt person', 'make bomb', 'making bomb', 'arms',
            'ammunition', 'ied', 'blast', 'detonation'
        ]
        if any(term in text_lower for term in security_terms):
            return 'Public Safety'

        best = max(scores, key=scores.get)
        return best if scores[best] > 0 else 'Other'

    def classify_category(self, text):
        """Main entry — DistilBERT first, keyword fallback"""
        # Always run keyword hard-override first for security terms
        text_lower = text.lower()
        security_terms = [
            'bomb', 'weapon', 'explosive', 'terror', 'terrorist',
            'kill', 'murder', 'gun', 'pistol', 'rifle', 'grenade',
            'militant', 'insurgent', 'extremist', 'hurt people',
            'arms', 'ammunition', 'ied', 'blast'
        ]
        if any(term in text_lower for term in security_terms):
            return 'Public Safety'

        if self._load_distilbert():
            result = self.classify_category_distilbert(text)
            if result:
                return result

        return self.classify_category_keywords(text)

    # ─────────────────────────────────────────────────────────────
    # PRIORITY DETECTION  ← THE MAIN FIX
    # ─────────────────────────────────────────────────────────────

    def detect_priority(self, text, category=None):
        """
        Multi-factor priority detection.

        EXECUTION ORDER:
          Step 1 → Category-based INSTANT override (Public Safety = High)
          Step 2 → Critical pattern matching (weapons/bombs/fire/death etc.)
          Step 3 → Contextual duration/scope rules
          Step 4 → Config keyword lists
          Step 5 → Medium contextual rules
          Step 6 → Medium keyword list
          Step 7 → Urgency phrase check
          Step 8 → Default = Low
        """
        text_lower = text.lower()

        # ── Step 1: Category-based instant override ───────────────
        # Run category detection FIRST so the boost works correctly
        if category is None:
            category = self.classify_category(text)

        if CATEGORY_PRIORITY_FLOOR.get(category) == 'High':
            return 'High'

        # ── Step 2: INSTANT HIGH — critical pattern match ─────────
        for pattern in INSTANT_HIGH_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return 'High'

        # ── Step 3: Contextual HIGH rules ─────────────────────────
        for pattern, condition_fn in CONTEXTUAL_HIGH_RULES:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match and condition_fn(match):
                return 'High'

        # ── Step 4: Config keyword HIGH ───────────────────────────
        for keyword in HIGH_PRIORITY_KEYWORDS:
            if keyword in text_lower:
                return 'High'

        # ── Step 5: Category floor for Salary → Medium ────────────
        if CATEGORY_PRIORITY_FLOOR.get(category) == 'Medium':
            return 'Medium'

        # ── Step 6: Contextual MEDIUM rules ───────────────────────
        for pattern, condition_fn in CONTEXTUAL_MEDIUM_RULES:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match and condition_fn(match):
                return 'Medium'

        # ── Step 7: Config keyword MEDIUM ─────────────────────────
        for keyword in MEDIUM_PRIORITY_KEYWORDS:
            if keyword in text_lower:
                return 'Medium'

        # ── Step 8: Urgency phrases ────────────────────────────────
        urgency_phrases = [
            'since yesterday', 'last night', 'this morning', 'whole day',
            'all day', 'no relief', 'still not', 'yet to', 'waiting for',
            'no response', 'already complained', 'again and again',
            'nobody is listening', 'no action taken', 'please help'
        ]
        if any(phrase in text_lower for phrase in urgency_phrases):
            return 'Medium'

        # ── Step 9: Very short complaint = likely real issue ──────
        if len(text.split()) < 10:
            return 'Medium'

        return 'Low'

    # ─────────────────────────────────────────────────────────────
    # FULL ANALYSIS
    # ─────────────────────────────────────────────────────────────

    def analyze_complaint(self, text):
        """
        Returns category + priority.
        Category is determined FIRST so priority can use it.
        """
        category = self.classify_category(text)
        priority = self.detect_priority(text, category=category)

        return {
            'category': category,
            'priority': priority
        }


# ── Global singleton ──────────────────────────────────────────────
_classifier = None

def get_classifier():
    global _classifier
    if _classifier is None:
        _classifier = ComplaintClassifier()
    return _classifier
