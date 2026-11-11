# Learn A2A by doing: a banking interview lab

Allow 45–60 minutes. Uses Python 3.12, official `a2a-sdk==1.3.0`, and A2A protocol 1.0. No LLM or API key is needed: both agent roles use deterministic code so you can see the communication clearly. This is a minimal client and specialist service, not two autonomous LLM agents.

## 1. Understand the problem (5 minutes)

A customer disputes a payment. A bank support agent delegates a payment review to an independently hosted specialist. The specialist owns its records and rules; the client sees its public interface and returned report.

```text
You → Bank support client → A2A over HTTP → Payment review specialist
                                             ↓
                                       Synthetic records
You ← Task status + report ←──────────────────┘
```

A2A standardizes discovery and communication between agents. It does not supply the intelligence, decide banking policy, or automatically authorize a transaction.

| Concept | Meaning | Find it in this lab |
|---|---|---|
| Agent Card | Public description of an agent, skills, endpoints and capabilities | `card` in server.py |
| Skill | An advertised ability; not an executable function definition | `review_payment` |
| Message | A unit of communication, containing parts | Client sends text `TX200` |
| Task | A tracked unit of work with an ID and status | Created in `execute()` |
| Context ID | Groups related interactions | Printed in the response; this lab uses one turn |
| Artifact | A work product | `payment-review.json`, carried as text |
| Streaming | Incremental delivery of updates | `--stream` |

## 2. Run the specialist (5 minutes)

Open a terminal:

```bash
cd /Users/macbookair/mcp_demo/a2a_bank_lab
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python server.py
```

If you use the environment already created for you, activation and `python server.py` are enough. Leave this terminal running. If port 9999 is occupied, stop the previous lab server first.

In another terminal:

```bash
cd /Users/macbookair/mcp_demo/a2a_bank_lab
source .venv/bin/activate
curl http://127.0.0.1:9999/.well-known/agent-card.json
```

Find the agent's name, skill, endpoint and streaming capability. Discovery describes an agent; it does not prove that the agent is trustworthy.

## 3. Delegate work (10 minutes)

In the second terminal:

```bash
python client.py TX200
python client.py TX100
python client.py TX999
```

Expected report outcomes:

| Input | Outcome | Why |
|---|---|---|
| TX200 | `manual_review` | AED 12,000 and unfamiliar device |
| TX100 | `no_demo_risk_flags` | AED 75 and recognized device |
| TX999 | `not_found` | No synthetic record |

Find the task ID and report in each response. No payment is approved, blocked or changed. These made-up thresholds are teaching rules, not bank policy.

Before continuing, explain aloud: What did the client send? What did the server return? Which part is A2A and which part is banking logic?

## 4. Watch the task lifecycle (10 minutes)

```bash
python client.py TX200 --stream
```

Observe: submitted task → working update → artifact update → completed update. This example completes quickly; streaming is about incremental delivery, not necessarily token generation.

**Critical distinction:** the task is completed even when the report says manual review. Protocol status describes execution; the artifact describes the business outcome. Likewise, `not_found` is a completed lookup here, not a transport failure.

## 5. Make a change yourself (10 minutes)

1. Add `TX300` to `PAYMENTS` in server.py: amount 200, currency AED, recognized device False.
2. Predict its outcome before running it.
3. Restart the server with Ctrl+C, then `python server.py`.
4. Run `python client.py TX300 --stream`.
5. Explain why a small payment still needs manual review under these demo rules.

Then change the rule from `or` to `and`. Predict which cases change, restart, and rerun. You changed the specialist's internal logic without changing the client or A2A contract.

Read client.py first, then `card`, then `execute()` in server.py. The SDK supplies protocol handling; your executor supplies domain behavior.

## 6. Practice for the bank interview (10 minutes)

**What is A2A?** An open protocol that allows independently implemented agents to discover capabilities, exchange messages, and track delegated work and outputs.

**Why not just REST?** A custom REST endpoint could do this lookup. A2A provides shared agent interaction semantics, including cards, tasks and artifacts, reducing custom integration across compatible agent systems. It still uses network transports; it is not an alternative to HTTP itself.

**A2A versus MCP?** A2A connects the support agent to the specialist. MCP could connect that specialist to a payment lookup tool. They can work together. This lab uses an in-memory dictionary instead of an MCP tool.

**Does an agent need an LLM?** The protocol does not require an LLM. Deterministic behavior makes this lab easy to inspect. A real agent could use an LLM internally while keeping the same external protocol.

**What would a bank need beyond this lab?** Authenticated service identities; authorization tied to the requesting user and task; encrypted transport; minimal customer data; audit records with correlation IDs and redaction; durable task storage; explicit timeouts and retry rules; and policy or human approval for sensitive actions. Advertising security in a card does not enforce it: the server must validate credentials and permissions.

**What if a request is retried?** A message or task ID is not a substitute for business idempotency. A payment-changing operation needs a deduplication key and durable outcome tracking to prevent duplicate effects.

**What if the task needs more information?** A2A supports richer task interactions. A follow-up exercise is to return an input-required state, accept a follow-up tied to the task/context, and resume. This one-turn lab does not implement that flow, cancellation, authentication or restart recovery.

**How would you summarize your demo?** “I built a support client and a payment-review specialist using the official A2A SDK. The client discovers an Agent Card, delegates a payment ID, and observes task updates and a report artifact. I separated task completion from the business outcome and used synthetic records. For a bank deployment I would add identity, authorization, durable state, auditability and business idempotency.”

## References and validation

- Official protocol documentation: https://a2a-protocol.org/v1.0.0/
- Official Python sample: https://github.com/a2aproject/a2a-samples/tree/main/samples/python/agents/helloworld
- Official SDK: https://github.com/a2aproject/a2a-python

Verified locally with SDK 1.3.0: card discovery; TX100, TX200 and unknown-ID requests; and streamed task/status/artifact events. The server binds only to localhost and stores tasks in memory. Stop it with Ctrl+C when finished.
