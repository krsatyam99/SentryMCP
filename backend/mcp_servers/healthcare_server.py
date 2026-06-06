import sys
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Healthcare Compliance Server")

MOCK_PATIENT_RECORDS = {
    "PAT-204B": {
        "patient_name": "Avery Johnson",
        "consent_status": "EXPIRED",
        "phi_exposure": "POSSIBLE",
        "open_alerts": ["Medication allergy missing acknowledgement"]
    },
    "PAT-101A": {
        "patient_name": "John Doe",
        "consent_status": "ACTIVE",
        "phi_exposure": "NONE",
        "open_alerts": []
    },
    "PAT-305C": {
        "patient_name": "Eleanor Vance",
        "consent_status": "REVOKED",
        "phi_exposure": "HIGH",
        "open_alerts": ["Unauthorized portal login detected", "Data export attempted"]
    },
    "PAT-408D": {
        "patient_name": "Marcus Aurelius",
        "consent_status": "ACTIVE",
        "phi_exposure": "NONE",
        "open_alerts": ["Missing signature on privacy practices form"]
    },
    "PAT-512E": {
        "patient_name": "Satyam Kumar",
        "consent_status": "ACTIVE",
        "phi_exposure": "NONE",
        "open_alerts": []
    },
    "PAT-619F": {
        "patient_name": "Sarah Connor",
        "consent_status": "RESTRICTED",
        "phi_exposure": "POSSIBLE",
        "open_alerts": ["Law enforcement record access request pending"]
    },
    "PAT-722G": {
        "patient_name": "Bruce Wayne",
        "consent_status": "ACTIVE",
        "phi_exposure": "MINIMAL",
        "open_alerts": ["VIP tracking flag enabled"]
    },
    "PAT-834H": {
        "patient_name": "Peter Parker",
        "consent_status": "EXPIRED",
        "phi_exposure": "HIGH",
        "open_alerts": ["Medical history transmitted over unencrypted email channel"]
    },
    "PAT-941I": {
        "patient_name": "Diana Prince",
        "consent_status": "ACTIVE",
        "phi_exposure": "NONE",
        "open_alerts": []
    },
    "PAT-055J": {
        "patient_name": "Walter White",
        "consent_status": "REVOKED",
        "phi_exposure": "HIGH",
        "open_alerts": ["Billing audit hold active", "Frequent pharmacy overrides flagged"]
    }
}


@mcp.tool()
def audit_patient_record(patient_id: str) -> str:
    """Audits a patient record for basic privacy and clinical compliance signals."""
    print(f"[Healthcare Subprocess] Auditing request received for: {patient_id}", file=sys.stderr)

    patient = MOCK_PATIENT_RECORDS.get(patient_id.upper())
    if not patient:
        return f"Error: Patient identifier '{patient_id}' was not found."
    
    # Format compliance alerts
    alerts_summary = "\n".join([f"  - {alert}" for alert in patient['open_alerts']]) if patient['open_alerts'] else "  (No open alerts)"

    return (
        f"Patient Name: {patient['patient_name']}\n"
        f"Consent Status: {patient['consent_status']}\n"
        f"PHI Exposure Level: {patient['phi_exposure']}\n"
        f"Open Compliance Alerts ({len(patient['open_alerts'])}):\n{alerts_summary}"
    )


if __name__ == "__main__":
    mcp.run()
