# N Green LeadOS — AI Coding Agent Prompt Kit

Use this pack to build a high-quality SaaS MVP step by step, not in a single generation.

## Files
- `MASTER_PROMPT.md`: permanent business, design, tech and engineering instructions. This is the complete build specification.
- `PHASE_BY_PHASE_PROMPTS.md`: ten individually copyable commands for Phase 0 through Phase 9.
- `reference_accounts.json`: exact product-category associations from the provided reference screenshot. These are *unverified research targets*.

## How to use
1. Create a new repository in your AI coding agent's workspace (Cursor, Claude Code, Copilot, Codex, etc.).
2. Upload all three files. Optionally also upload the existing `N_Green_LeadOS_MVP.zip` to allow the agent to inspect/reuse the older prototype.
3. Paste only the **START COMMAND** from the top of `MASTER_PROMPT.md` or Phase 0 from `PHASE_BY_PHASE_PROMPTS.md`.
4. Verify the initial architecture and tests; then paste the Phase 1 command.
5. Continue one phase at a time. Never give provider API keys in public prompts, screenshots or Git history.

## Required development environment
- Windows PowerShell + Git, Python 3.12/3.13 with compatible dependencies, Node.js supported LTS, Docker Desktop with Linux containers, and a code editor/AI coding agent.
- API keys not required for Phases 0–3 while search stays on the DEMO adapter, or for the mock portions of later phases.
- Serper, Supabase and Vapi accounts/credentials are separately obtained when their phases are approved.

## Why this scope
The client wants **lead research from the internet + manual leads + AI calling + CRM**, not a complete manufacturing ERP in the first release. The document defines exactly that sales-tech MVP while keeping future integration options open.
