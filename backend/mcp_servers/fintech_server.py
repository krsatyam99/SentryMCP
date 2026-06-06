import sys
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP for the FinTech track
mcp = FastMCP("FinTech Compliance Server")

# Mock database ledger for our proof-of-concept
MOCK_LEDGER = {
    "ACC-991A": {
        "account_holder": "Global Logistics Corp",
        "risk_score": "HIGH",
        "recent_transactions": [
            {"id": "TX-101", "amount": 500000, "flagged": True, "country": "Offshore"},
            {"id": "TX-102", "amount": 1200, "flagged": False, "country": "Domestic"}
        ],
        "compliance_status": "UNDER_REVIEW"
    },
    "ACC-442B": {
        "account_holder": "Apex Health Solutions",
        "risk_score": "LOW",
        "recent_transactions": [
            {"id": "TX-201", "amount": 45000, "flagged": False, "country": "Domestic"},
            {"id": "TX-202", "amount": 8900, "flagged": False, "country": "Domestic"}
        ],
        "compliance_status": "CLEARED"
    },
    "ACC-773C": {
        "account_holder": "Vanguard Ventures LLC",
        "risk_score": "MEDIUM",
        "recent_transactions": [
            {"id": "TX-301", "amount": 120000, "flagged": False, "country": "Domestic"},
            {"id": "TX-302", "amount": 95000, "flagged": True, "country": "Offshore"},
            {"id": "TX-303", "amount": 3100, "flagged": False, "country": "Domestic"}
        ],
        "compliance_status": "UNDER_REVIEW"
    },
    "ACC-104D": {
        "account_holder": "Nova Retail Group",
        "risk_score": "HIGH",
        "recent_transactions": [
            {"id": "TX-401", "amount": 850000, "flagged": True, "country": "Offshore"},
            {"id": "TX-402", "amount": 920000, "flagged": True, "country": "Offshore"}
        ],
        "compliance_status": "SUSPENDED"
    },
    "ACC-555E": {
        "account_holder": "Satyam Tech Consulting",
        "risk_score": "LOW",
        "recent_transactions": [
            {"id": "TX-501", "amount": 2500, "flagged": False, "country": "Domestic"}
        ],
        "compliance_status": "CLEARED"
    },
    "ACC-226F": {
        "account_holder": "Horizon Real Estate",
        "risk_score": "HIGH",
        "recent_transactions": [
            {"id": "TX-601", "amount": 1200000, "flagged": False, "country": "Domestic"},
            {"id": "TX-602", "amount": 450000, "flagged": True, "country": "Offshore"}
        ],
        "compliance_status": "UNDER_REVIEW"
    },
    "ACC-887G": {
        "account_holder": "Starlight Entertainment",
        "risk_score": "LOW",
        "recent_transactions": [
            {"id": "TX-701", "amount": 15000, "flagged": False, "country": "Domestic"},
            {"id": "TX-702", "amount": 22000, "flagged": False, "country": "Domestic"},
            {"id": "TX-703", "amount": 18500, "flagged": False, "country": "Domestic"}
        ],
        "compliance_status": "CLEARED"
    },
    "ACC-338H": {
        "account_holder": "Alpha Crypto Exchange",
        "risk_score": "HIGH",
        "recent_transactions": [
            {"id": "TX-801", "amount": 3000000, "flagged": True, "country": "Offshore"},
            {"id": "TX-802", "amount": 2500000, "flagged": True, "country": "Offshore"},
            {"id": "TX-803", "amount": 4100000, "flagged": True, "country": "Offshore"}
        ],
        "compliance_status": "SUSPENDED"
    },
    "ACC-999I": {
        "account_holder": "Delta Manufacturing",
        "risk_score": "MEDIUM",
        "recent_transactions": [
            {"id": "TX-901", "amount": 65000, "flagged": False, "country": "Domestic"},
            {"id": "TX-902", "amount": 72000, "flagged": False, "country": "Domestic"}
        ],
        "compliance_status": "CLEARED"
    },
    "ACC-110J": {
        "account_holder": "Beacon Non-Profit Corp",
        "risk_score": "MEDIUM",
        "recent_transactions": [
            {"id": "TX-001", "amount": 50000, "flagged": True, "country": "Offshore"},
            {"id": "TX-002", "amount": 55000, "flagged": False, "country": "Domestic"}
        ],
        "compliance_status": "UNDER_REVIEW"
    }
}
@mcp.tool()
def audit_financial_account(account_id: str) -> str:
    """
    Audits a specific financial ledger account for compliance anomalies.
    """
    print(f"[FinTech Subprocess] Auditing request received for: {account_id}", file=sys.stderr)
    
    account = MOCK_LEDGER.get(account_id.upper())
    if not account:
        return f"Error: Account identifier '{account_id}' was not found."
    
    # Format recent transactions with amounts
    transactions_summary = "\n".join([
        f"  - {tx['id']}: ${tx['amount']:,} ({tx['country']}) {'[FLAGGED]' if tx['flagged'] else ''}"
        for tx in account['recent_transactions']
    ])
        
    return (
        f"Account Holder: {account['account_holder']}\n"
        f"Risk Profile: {account['risk_score']}\n"
        f"Compliance Status: {account['compliance_status']}\n"
        f"Recent Transactions:\n{transactions_summary}"
    )

if __name__ == "__main__":
    mcp.run()