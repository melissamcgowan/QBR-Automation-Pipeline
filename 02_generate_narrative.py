"""
02_generate_narrative.py

Turns structured account data into QBR narrative text -- an executive
summary, a trend read, and a recommendation -- using a rules engine
that mirrors how you'd structure a prompt to an LLM for this task.

NOTE ON PRODUCTION USE: this script uses templated/rule-based logic
so the project runs completely offline with no API dependency. In a
real deployment, you'd swap generate_exec_summary() for a call to the
Anthropic or OpenAI API, passing the same structured account data as
context and asking the model to draft the narrative in your team's
voice. The rest of the pipeline (data -> narrative -> PDF) stays
identical either way -- that's the point of separating this step out.

Run: python3 02_generate_narrative.py
Output: qbr_accounts_with_narrative.json
"""

import json

with open("qbr_accounts.json") as f:
    accounts = json.load(f)


def trend_direction(series):
    delta = series[-1] - series[0]
    if delta > 8:
        return "improving"
    elif delta < -8:
        return "declining"
    return "stable"


def generate_exec_summary(acct):
    name = acct["name"]
    band = acct["current_health_band"]
    direction = trend_direction(acct["health_score_by_quarter"])
    delta = acct["health_score_by_quarter"][-1] - acct["health_score_by_quarter"][0]

    if band in ("Healthy",) and direction == "improving":
        tone = (f"{name} enters this QBR in strong standing. Health score has climbed "
                f"{delta:.0f} points over the last four quarters, and the account shows "
                f"consistent engagement across usage and relationship signals.")
    elif band in ("Critical", "At Risk") and direction == "declining":
        tone = (f"{name} requires immediate attention. Health score has dropped "
                f"{abs(delta):.0f} points over the last four quarters, moving the account "
                f"into the {band} band. This QBR should focus on a recovery plan, not "
                f"a standard business review.")
    elif direction == "stable":
        tone = (f"{name} has held steady at a {band.lower()} level over the past year, "
                f"with no major swings in engagement. This is a good QBR to probe for "
                f"upsell/expansion signals or unaddressed friction.")
    else:
        article = "an" if direction[0] in "aeiou" else "a"
        tone = (f"{name} is currently in the {band} band with {article} {direction} trend "
                f"({delta:+.0f} points over four quarters). Worth a closer look at what's "
                f"driving the shift before the renewal conversation.")
    return tone


def generate_recommendation(acct):
    band = acct["current_health_band"]
    has_risks = len(acct["risks"]) > 0
    days_to_renewal = acct["renewal_in_days"]

    if band == "Critical":
        rec = ("Escalate to a save-play: schedule an executive-to-executive call within "
               "2 weeks, and involve your manager before the renewal conversation.")
    elif band == "At Risk" and has_risks:
        rec = ("Address the top risk factor directly with the account before discussing "
               "renewal terms. Consider a mid-cycle check-in rather than waiting for the QBR.")
    elif band == "Healthy" and not has_risks:
        rec = ("Use this QBR to explore expansion -- additional seats, modules, or a "
               "case study/reference ask, given the strength of the relationship.")
    else:
        rec = ("Standard QBR cadence is appropriate. Reconfirm success metrics and "
               "surface any early risk signals before they compound.")

    if days_to_renewal <= 45 and band in ("Critical", "At Risk"):
        rec += f" Renewal is in {days_to_renewal} days -- treat this as time-sensitive."
    return rec


for acct in accounts:
    acct["narrative"] = {
        "executive_summary": generate_exec_summary(acct),
        "recommendation": generate_recommendation(acct),
        "trend_direction": trend_direction(acct["health_score_by_quarter"]),
    }

with open("qbr_accounts_with_narrative.json", "w") as f:
    json.dump(accounts, f, indent=2)

print(f"Generated narratives for {len(accounts)} accounts -> qbr_accounts_with_narrative.json\n")
for a in accounts:
    print(f"### {a['name']} ({a['current_health_band']})")
    print(f"Summary: {a['narrative']['executive_summary']}")
    print(f"Recommendation: {a['narrative']['recommendation']}\n")
