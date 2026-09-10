"""
ClinicalTrials.gov API v2 — one-off sample puller.

Free, local, no scheduling and no delta/change-tracking. See README.md for what
this stub deliberately does NOT do, and for the production actor that adds it.
"""
import json
import sys
import requests

API_BASE = "https://clinicaltrials.gov/api/v2/studies"


def fetch_trials(condition: str, max_results: int = 20):
    params = {
        "query.cond": condition,
        "pageSize": min(max_results, 100),
        "format": "json",
    }
    try:
        resp = requests.get(API_BASE, params=params, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching from ClinicalTrials.gov: {e}", file=sys.stderr)
        return []

    data = resp.json()
    studies = data.get("studies", [])[:max_results]

    records = []
    for study in studies:
        protocol = study.get("protocolSection", {})
        identification = protocol.get("identificationModule", {})
        status = protocol.get("statusModule", {})
        sponsor = protocol.get("sponsorCollaboratorsModule", {}).get("leadSponsor", {})
        conditions = protocol.get("conditionsModule", {}).get("conditions", [])
        design = protocol.get("designModule", {})

        records.append({
            "nct_id": identification.get("nctId"),
            "brief_title": identification.get("briefTitle"),
            "overall_status": status.get("overallStatus"),
            "last_update_post_date": status.get("lastUpdatePostDateStruct", {}).get("date"),
            "status_verified_date": status.get("statusVerifiedDate"),
            "lead_sponsor": sponsor.get("name"),
            "conditions": conditions,
            "phases": design.get("phases", []),
        })
    return records


if __name__ == "__main__":
    condition = sys.argv[1] if len(sys.argv) > 1 else "diabetes"
    max_results = int(sys.argv[2]) if len(sys.argv) > 2 else 20

    print(f"Fetching up to {max_results} trials for condition: {condition!r}")
    records = fetch_trials(condition, max_results)

    if not records:
        print("No records returned (or request failed).")
        sys.exit(1)

    out_path = "sample_output.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)

    print(f"Wrote {len(records)} real trial records to {out_path}")
    print(json.dumps(records[0], indent=2))
