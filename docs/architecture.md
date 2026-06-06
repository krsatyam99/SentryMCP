# Architecture Overview

This MVP uses a small clean-architecture shape so the demo is easy to explain and extend.

## Runtime Flow

```text
POST /analyze
    -> AuditRequest
    -> AnalyzeVoiceUseCase
    -> IMcpClientPort
    -> MCP domain server
    -> ILlmPort
    -> structured verdict
```

## Layers

- `src/agentai/core`: domain entity, use case, and abstract ports.
- `src/agentai/adapters/inbound/api`: FastAPI HTTP entrypoint.
- `src/agentai/adapters/outbound/mcp`: MCP client adapter and routing logic.
- `src/agentai/adapters/outbound/aws`: Bedrock-compatible LLM adapter with local demo mode.
- `backend/mcp_servers`: domain-specific MCP servers for FinTech, Healthcare, and HR.

## Design Choices

- The use case does not know about FastAPI, boto3, or MCP implementation details.
- Each industry has its own MCP server and tool, which makes the routing visible in demos.
- `LLM_PROVIDER=local` guarantees the demo works without cloud quota.
- `LLM_PROVIDER=bedrock` keeps the project ready for AWS Bedrock when quota is available.

## MVP Scope

This project intentionally focuses on a working backend demo:

- no frontend yet
- no production authentication yet
- no real customer or patient data
- no paid cloud dependency required for the demo path

Future extensions can add a voice UI, CI/CD, CloudFront hosting, and AgentCore deployment once the core agent story is stable.
