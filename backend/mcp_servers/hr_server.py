import sys
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("HR Policy Server")

MOCK_POLICIES = {
    "leave": {
        "title": "Employee Leave Policy",
        "eligibility": "Full-time employees after 90 days",
        "summary": "Employees receive 18 annual leave days, 10 sick leave days, and manager-approved emergency leave.",
        "risk_note": "Escalate if leave denial involves medical, maternity, disability, or protected-category concerns."
    },
    "remote": {
        "title": "Remote Work Policy",
        "eligibility": "Role-dependent with manager approval",
        "summary": "Employees may work remotely up to 3 days per week when data security and coverage requirements are met.",
        "risk_note": "Escalate if policy exceptions are applied inconsistently across teams."
    },
    "whistleblower": {
        "title": "Whistleblower and Non-Retaliation Policy",
        "eligibility": "All employees, contractors, and third-party vendors",
        "summary": "Provides anonymous channels to report suspected financial fraud, ethical violations, or harassment without fear of retaliation.",
        "risk_note": "CRITICAL: Any breach of reporter anonymity or hint of professional retaliation requires immediate legal escalation."
    },
    "insider_trading": {
        "title": "Securities Trading and Blackout Windows",
        "eligibility": "All executive staff, directors, and finance department employees",
        "summary": "Prohibits trading company stock outside of approved windows or while in possession of material non-public information (MNPI).",
        "risk_note": "CRITICAL: Flag immediately if an employee trades during a designated corporate blackout period."
    },
    "data_privacy": {
        "title": "Global Data Protection and GDPR Compliance",
        "eligibility": "All employees handling customer or internal personal data",
        "summary": "Requires explicit user consent, minimal data retention, and strict encryption protocols for storing or transferring personally identifiable information (PII).",
        "risk_note": "HIGH: Escalate if customer data is transferred outside approved geographical boundaries without explicit consent."
    },
    "it_security": {
        "title": "Acceptable Use and Asset Security Policy",
        "eligibility": "All personnel accessing company networks or hardware",
        "summary": "Mandates multi-factor authentication (MFA), forbids downloading unapproved third-party software, and bans using public Wi-Fi without a corporate VPN.",
        "risk_note": "HIGH: Flag instances where active root access or system credentials are shared via unencrypted chat channels."
    },
    "satyam_consulting_sla": {
        "title": "Satyam Tech Consulting Engagement Guidelines",
        "eligibility": "Internal procurement and external engineering contractors",
        "summary": "Defines operational baselines including 99.9% uptime commitments, standard secure code review requirements, and strict code IP ownership boundaries.",
        "risk_note": "CLEARED: Standard operating procedure. Ensure all external contractor code repositories undergo automated compliance scanning."
    },
    "anti_bribery": {
        "title": "Anti-Bribery and Corruption (ABC) Policy",
        "eligibility": "All staff, particularly procurement, international sales, and logistics",
        "summary": "Strictly prohibits offering, giving, or receiving gifts, entertainment, or payments to influence corporate or government decisions. Caps promotional gifts at $50.",
        "risk_note": "CRITICAL: Investigate any corporate expense categorized as 'facilitation payment' or high-value client entertainment without pre-approval."
    },
    "expense_reimbursement": {
        "title": "Corporate Expense and Travel Policy",
        "eligibility": "Active employees traveling on authorized company business",
        "summary": "Reimburses actual business expenses for travel, meals, and accommodations up to daily limits ($75/day for meals). Receipts required for items over $25.",
        "risk_note": "MEDIUM: Flag recurring expense submissions that fall just under the $25 receipt requirement threshold."
    },
    "social_media": {
        "title": "Public Communications and Social Media Policy",
        "eligibility": "All employees representing themselves as corporate affiliates",
        "summary": "Prohibits employees from speaking on behalf of the company, revealing trade secrets, or posting discriminatory content that damages corporate reputation.",
        "risk_note": "MEDIUM: Escalate if an unapproved employee posts sensitive operational data or speculative product timelines publicly."
    }
}

@mcp.tool()
def summarize_hr_policy(policy_topic: str) -> str:
    """Summarizes an HR policy and highlights compliance-sensitive notes."""
    print(f"[HR Subprocess] Policy summary request received for: {policy_topic}", file=sys.stderr)

    topic = policy_topic.lower()
    policy = MOCK_POLICIES.get(topic)
    if not policy:
        available = ", ".join(sorted(MOCK_POLICIES))
        return f"Error: Policy topic '{policy_topic}' was not found. Available topics: {available}."

    return (
        f"Policy: {policy['title']}\n"
        f"Eligibility: {policy['eligibility']}\n"
        f"Summary: {policy['summary']}\n"
        f"Compliance Note: {policy['risk_note']}"
    )


if __name__ == "__main__":
    mcp.run()
