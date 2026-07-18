"""
01_generate_qbr_data.py

Generates 4 quarters of historical data for a set of sample accounts
that are due for a QBR this cycle. In production, this would pull from
your CRM, product analytics, support tool, and billing system -- the
same sources as the health score project, but tracked over time
instead of as a single snapshot.

Run: python3 01_generate_qbr_data.py
Output: qbr_accounts.json
"""

import json
import numpy as np

np.random.seed(7)

ACCOUNTS = [
    {"name": "Brightline Logistics", "segment": "Enterprise", "arr": 184000,
     "csm": "Melissa McGowan", "renewal_in_days": 62, "trend": "improving"},
    {"name": "Fernwood Health Group", "segment": "Enterprise", "arr": 96000,
     "csm": "Melissa McGowan", "renewal_in_days": 45, "trend": "declining"},
    {"name": "Aster & Co.", "segment": "Mid-Market", "arr": 38000,
     "csm": "Melissa McGowan", "renewal_in_days": 90, "trend": "flat"},
    {"name": "Northgate Retail Partners", "segment": "Mid-Market", "arr": 52000,
     "csm": "Melissa McGowan", "renewal_in_days": 30, "trend": "at_risk"},
    {"name": "Cobalt Manufacturing", "segment": "Enterprise", "arr": 210000,
     "csm": "Melissa McGowan", "renewal_in_days": 75, "trend": "improving"},
]

QUARTERS = ["Q3 2025", "Q4 2025", "Q1 2026", "Q2 2026"]

TREND_SHAPE = {
    # (start_health, end_health, start_usage, end_usage)
    "improving": (58, 82, 40, 78),
    "declining": (78, 42, 65, 30),
    "flat":      (65, 68, 50, 52),
    "at_risk":   (60, 31, 48, 18),
}


def build_quarterly_series(start, end, n, noise=3.0):
    base = np.linspace(start, end, n)
    noisy = base + np.random.normal(0, noise, n)
    return [round(max(0, min(100, v)), 1) for v in noisy]


def generate_wins_and_risks(trend, segment):
    win_pool = [
        "Expanded seat count after successful rollout to a second business unit",
        "Champion promoted internally and remains strong advocate",
        "Adopted the reporting/analytics module after Q1 enablement session",
        "Renewed early with a multi-year commitment",
        "Integrated our platform into their core workflow (Salesforce sync live)",
        "Positive feedback in latest NPS survey citing support responsiveness",
    ]
    risk_pool = [
        "Primary champion departed the company in the last quarter",
        "Usage concentrated in a shrinking subset of the licensed seats",
        "Two P1 support escalations in the last 60 days",
        "Budget scrutiny flagged by finance contact ahead of renewal",
        "Key integration has been broken/unused since last quarter",
        "No executive sponsor engagement in over 150 days",
    ]
    n_wins = {"improving": 3, "flat": 2, "declining": 1, "at_risk": 1}[trend]
    n_risks = {"improving": 0, "flat": 1, "declining": 2, "at_risk": 3}[trend]
    wins = list(np.random.choice(win_pool, size=n_wins, replace=False))
    risks = list(np.random.choice(risk_pool, size=n_risks, replace=False)) if n_risks else []
    return wins, risks


data = []
for acct in ACCOUNTS:
    sh, eh, su, eu = TREND_SHAPE[acct["trend"]]
    health_series = build_quarterly_series(sh, eh, len(QUARTERS))
    usage_series = build_quarterly_series(su, eu, len(QUARTERS), noise=4.0)
    tickets_series = [int(max(0, round(t))) for t in
                       np.linspace(2, 9 if acct["trend"] in ("declining", "at_risk") else 2,
                                   len(QUARTERS)) + np.random.normal(0, 1, len(QUARTERS))]
    wins, risks = generate_wins_and_risks(acct["trend"], acct["segment"])

    data.append({
        **acct,
        "quarters": QUARTERS,
        "health_score_by_quarter": health_series,
        "usage_score_by_quarter": usage_series,
        "support_tickets_by_quarter": tickets_series,
        "current_health_score": health_series[-1],
        "current_health_band": (
            "Healthy" if health_series[-1] >= 75 else
            "Neutral" if health_series[-1] >= 50 else
            "At Risk" if health_series[-1] >= 30 else "Critical"
        ),
        "wins": wins,
        "risks": risks,
    })

with open("qbr_accounts.json", "w") as f:
    json.dump(data, f, indent=2)

print(f"Generated QBR data for {len(data)} accounts -> qbr_accounts.json")
for a in data:
    print(f"  {a['name']:28s} health {a['health_score_by_quarter'][0]:>5.1f} -> "
          f"{a['current_health_score']:>5.1f}  ({a['current_health_band']})")
