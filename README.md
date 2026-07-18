# QBR Automation Pipeline

A portfolio project automating one of the most time-consuming recurring
tasks in customer success: preparing Quarterly Business Reviews.

## Why this project

A CSM managing 20-40 accounts can lose days each quarter pulling metrics,
building slides, and writing summaries for QBRs -- often for accounts
that don't need a deep-dive. This project automates the entire pipeline:
raw account data in, polished, presentation-ready PDF QBR documents out,
with the busy-work (data pulling, chart building, first-draft narrative)
handled automatically so the CSM's time goes into the actual customer
conversation instead of the deck.

## What it does

1. **`01_generate_qbr_data.py`** -- Generates 4 quarters of historical
   data for 5 sample accounts due for a QBR: health score trend, usage
   trend, support ticket volume, and account-specific wins/risks. (In
   production: pulled from CRM, product analytics, support tool, and
   billing.)

2. **`02_generate_narrative.py`** -- Converts structured data into QBR
   narrative text: an executive summary, trend read, and a recommended
   next step -- using a rules engine that mirrors how you'd structure a
   prompt to an LLM for this task. This step is intentionally isolated
   from the data and rendering steps so it's a drop-in swap for an
   actual LLM API call in production (see note in the script).

3. **`03_build_qbr_pdfs.py`** -- Renders one polished, print-ready PDF
   per account: key metrics table, health/usage trend chart, wins,
   risks, and a recommended next step -- the kind of document a CSM
   could walk into a customer meeting with.

## Results

Running the pipeline end-to-end produces 5 complete QBR documents from
a single command, each combining:
- A health-band-coded metrics summary table
- A 4-quarter trend chart (health score vs. usage score)
- An auto-generated executive summary calibrated to the account's
  trend direction and health band
- Wins and risks pulled directly from account data
- A recommendation that adapts to urgency (e.g., accounts in the
  Critical band with a renewal inside 45 days get an escalation
  recommendation with a specific timeline)

## How to run it

```bash
pip install pandas matplotlib numpy reportlab
python3 01_generate_qbr_data.py       # generates qbr_accounts.json
python3 02_generate_narrative.py      # generates qbr_accounts_with_narrative.json
python3 03_build_qbr_pdfs.py          # generates qbr_reports/*.pdf
```

## How this maps to a real CS org

- Swap the synthetic data generator for a script pulling from your
  CRM, product analytics, and support tool -- the account schema
  (`qbr_accounts.json`) is designed to be a straightforward mapping
  target for real data sources.
- Swap the rules-based narrative functions in `02_generate_narrative.py`
  for a call to the Anthropic or OpenAI API, passing the same
  structured account data as context. The rest of the pipeline is
  unaffected -- that separation is deliberate.
- Run this on a schedule (e.g., every Monday) filtered to accounts with
  a QBR or renewal coming up in the next N days, and auto-attach the
  PDF to the relevant CRM record or Slack channel.

## Extending this further

- Add a batch cover-page/index PDF summarizing all accounts due for
  QBR that quarter, for a leader-level rollup view.
- Feed the auto-generated recommendation into a task in your CRM or
  project tool, rather than just the PDF.
- Add a comparison to the prior quarter's QBR to highlight what
  actually changed since the last conversation.
