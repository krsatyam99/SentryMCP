# LinkedIn Demo Script — SentryMCP (90 Seconds)

**Duration:** ~90 seconds at a calm speaking pace  
**Tone:** Professional, confident, clear  
**Before recording:** Server running → http://localhost:8000/ → Chrome/Edge → `POLLY_ENABLED=true`

---

## Script

**[0:00 – 0:10 | Hook]**

> Hi, I'm **[Your Name]**. This is **SentryMCP** — a multi-domain compliance agent I built as an MVP.

**[0:10 – 0:25 | Business problem]**

> Compliance teams work across disconnected systems — financial ledgers, patient records, HR policies. Checking risk means switching tools and re-explaining context every time. SentryMCP gives operators **one interface** to ask audit questions in plain English or by voice — and get a **structured compliance verdict** in seconds.

**[0:25 – 0:45 | Architecture — show diagram or code briefly]**

> Under the hood: **FastAPI** receives the request, routes it through the **Model Context Protocol** to the right domain server — FinTech, Healthcare, or HR — pulls subsystem data, then **AWS Bedrock** reasons over it and returns CLEARED, FLAGGED, or ACTION_REQUIRED with a confidence score. New industries plug in by adding an MCP server — no rewrite of core logic.

**[0:45 – 1:10 | Live demo — screen recording]**

> Watch: I select **FinTech** and ask — *"Check account ACC-991A for possible fraud."* The MCP server returns ledger data. Bedrock flags high risk. **Amazon Polly** reads the verdict aloud.
>
> Follow-up — *"What about their flagged transactions?"* — the conversation remembers the account. I switch to **Healthcare**, same flow, different MCP tool.

**[1:10 – 1:30 | Close + future]**

> This is a portfolio POC today — clean architecture, mock data, swappable adapters. Next: real database connectors, enterprise auth, and cloud deployment. Built with Python, MCP, and AWS. **Link in the description.** Thanks for watching.

---

## Demo checklist (while recording)

- [ ] Open http://localhost:8000/
- [ ] FinTech → voice or text: *"Check account ACC-991A for possible fraud"*
- [ ] Show verdict + expand MCP logs (optional)
- [ ] Follow-up: *"What about their flagged transactions?"* (shows conversation memory)
- [ ] Switch Healthcare → *"Check patient PAT-204B for compliance risk"*
- [ ] Optional: flash http://localhost:8000/docs for API view

---

## On-screen text suggestions (optional captions)

| Timestamp | Caption |
|-----------|---------|
| 0:05 | SentryMCP — Multi-Domain Compliance Agent |
| 0:30 | MCP + Bedrock + Polly |
| 0:50 | FinTech audit → FLAGGED |
| 1:05 | Multi-turn conversation support |

---

## One-liner for LinkedIn post

> Built SentryMCP — a voice-enabled compliance agent that routes audit questions to domain MCP servers (FinTech, Healthcare, HR) and returns structured verdicts via AWS Bedrock + Polly. Clean architecture, pluggable domains, demo-ready. #AI #MCP #AWS #Python #Compliance
