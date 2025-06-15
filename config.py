DB_NAME = "sprint_06-06-2024.db"

# List of evaluation metrics. Change it as per need
# NOTE: You need to make sure that the initials of each word joined is always unique
# ....: as the intials get used to identify the fields uniquely
# For eg., Code Quality Metrics: cqm | Collaboration & Communication: cac | Work-Life Balance: wlb
# '&' becomes 'a' in shorthand. Also, '/' and '-' get replaced ' ' for word separation
METRIC_DESCRIPTIVE = {
    "• Code Quality Metrics": "",
    "• Development Efficiency": "",
    "• Collaboration & Communication": "",
    "• Learning and Growth": "",
    "• Task and Time Management": "",
    "• Customer/End-User Focus": "",
    "• Innovation and Initiative": "",
    "• Consistency and Reliability": "",
    "• Team Support & Mentorship": "",
    "• Work-Life Balance": "",
}

METRIC = list(METRIC_DESCRIPTIVE.keys())

# Reviewer name choices (human-readable name -> shortname (keys and values should be unique among themselves)). Modify it as per your need
REVIEWERS_SHORTHAND = {
    "Biltu Dey": "biltu",
    "Hardik Singh": "hardik",
    "Laxman Gaikwad": "laxman",
    "Prateek Kumar": "prateek",
    "Rohan Chinchkar": "rohan",
    "Tanish Goyal": "tanish",
    "Nischey Badyal": "nischey",
    "Vivek Tripathi": "vivek",
}

REVIEWERS_SHORTHAND_REV = {v: k for k, v in REVIEWERS_SHORTHAND.items()}

# If a reviewer need to be assigned only some person to review and not all. Also, those who won't be rated either
SELECTIVE_REVIEWERS = {
    "nischey": ["rohan"]
}

for rev in SELECTIVE_REVIEWERS:
    if rev not in REVIEWERS_SHORTHAND_REV:
        raise Exception(f"SELECTIVE_REVIEWER with shorthand {rev} doesn't match the expected REVIEWER_SHORTHAND names")
    else:
        for assigned in SELECTIVE_REVIEWERS[rev]:
            if assigned not in REVIEWERS_SHORTHAND_REV:
                raise Exception(f"SELECTIVE_REVIEWER with shorthand '{rev}' has unmatched assigned name '{assigned}' which is "
                                "not as per the expected REVIEWER_SHORTHAND names")
