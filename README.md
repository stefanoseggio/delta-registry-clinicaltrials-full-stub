# Delta Registry — ClinicalTrials.gov Sample Puller

A free, local, one-off sample puller for ClinicalTrials.gov API v2 trial data. This is a stub, not the production actor — see "What this doesn't do" below before assuming it's a drop-in replacement.

## What this does

`main.py` calls the real, public ClinicalTrials.gov API v2 (`https://clinicaltrials.gov/api/v2/studies`), filters by condition (`query.cond`), and writes up to 100 real trial records to `sample_output.json`. No API key required — this endpoint is free and unauthenticated.

## Setup

```bash
pip install -r requirements.txt
python main.py "non-small cell lung cancer" 20
```

First argument is the condition filter, second is the max number of records (default 20, capped at 100 per the API's own page size limit).

## Real example output

A real record this script produces (from an actual run against the live API):

```json
{
  "nct_id": "NCT05823948",
  "brief_title": "A Study Using Flash Glucose Measurements for a New Once-weekly Insulin (Insulin Icodec) in People With Type 2 Diabetes Who Have Not Used Insulin Before (ONWARDS 9)",
  "overall_status": "COMPLETED",
  "last_update_post_date": "2026-04-30",
  "status_verified_date": "2026-04",
  "lead_sponsor": "Novo Nordisk A/S",
  "conditions": ["Diabetes Mellitus, Type 2"],
  "phases": ["PHASE3"]
}
```

## The real delta engine (not implemented here — documented for context)

The production actor this stub funnels to runs a genuinely different mechanism, not just a bigger version of this script:

- **Fingerprinting**: the tracked ClinicalTrials.gov fields (`overall_status`, `last_update_post_date`, `status_verified_date`) are flat strings, pipe-joined and hashed (SHA-256) into a fingerprint per trial — no serialization step is needed there since there's no nested data on the trial side.
- **Cross-run state**: each trial's fingerprint is persisted in a **named** Apify key-value store that survives between scheduled runs — not the run-scoped state a one-off script like this one has no equivalent of.
- **Classification**: every run compares the current fingerprint against the last-seen one and classifies the record as `NEW_TRIAL`, `STATUS_CHANGE`, or nothing at all in delta mode — an unchanged trial is never re-delivered and never billed.
- **A second independent source**: the production actor also tracks FDA Orange Book patent/exclusivity data (`applNo`/`productNo`-keyed), with its own `NEW_LISTING`/`PATENT_EXCLUSIVITY_CHANGE` events — not covered by this stub at all. Its `patent_data` field *is* a nested object whose key order isn't guaranteed stable across fetches, so that fingerprint (unlike the trial one) is built from a recursive, deterministic JSON serialization that sorts keys at every nesting level, not just the top level, before hashing. A naive `JSON.stringify(obj, Object.keys(obj).sort())` only sorts top-level keys and produces a non-deterministic hash for nested objects — the production actor's Orange Book fingerprinting was built (and a real bug fixed) specifically to avoid that.
- **Reliability**: full-jitter exponential backoff on retries, and a dead-letter queue for exhausted attempts, so a transient ClinicalTrials.gov API failure doesn't silently drop data.

## What this doesn't do

No scheduling, no delta/change-tracking between runs, no FDA Orange Book source, no retry/backoff, no dead-letter queue. Every run pulls a fresh, full snapshot — there's no "only what changed" mode here, and running this twice in a row will just fetch the same records again.

## The production actor

For scheduled runs, real fingerprint-based delta tracking (NEW_TRIAL/STATUS_CHANGE events only, unchanged trials never re-billed), the FDA Orange Book source, and full reliability guarantees: **https://apify.com/stefano_seggio/actor-24-clinical-trials-delta-engine**

Pay-per-event: $0.002 per new/changed record, $0.00005 per run start.

## License

MIT - see [LICENSE](LICENSE). This sample script is free and unrestricted;
it is not the production actor's source.
