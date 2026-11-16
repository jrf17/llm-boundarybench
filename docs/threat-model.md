# Threat Model

## System under analysis

A synthetic customer-support assistant with access to:

- a document corpus (retrieval),
- a synthetic contact directory (lookup),
- a simulated email tool, and
- a simulated data-export tool.

The assistant should answer questions, retrieve documents, look up contacts,
and — only when the user explicitly authorizes it — send email. It must never
export data to an attacker-controlled destination and must never disclose
protected synthetic markers.

## Trust model

| Input | Trust | Controlled by |
| --- | --- | --- |
| System prompt / application policy | Trusted | application owner |
| User prompt | Untrusted | end user (attacker) |
| Retrieved document content | Untrusted | data source (attacker) |
| Tool output | Untrusted | upstream system (attacker) |
| Tool invocation | Partially trusted | application + model |

## Attacker capabilities

The attacker can:

- submit arbitrary text as the user prompt;
- control the content of documents that enter the retrieval corpus;
- control the output of simulated tools that return attacker-influenced data;
- maintain a multi-turn conversation.

The attacker **cannot** directly modify application code, the system prompt, or
the authorization policy — which is precisely why the hardened application moves
enforcement there.

## Security objectives

1. **Instruction hierarchy** — attacker text must not override application
   policy.
2. **Retrieval boundary** — retrieved content is data, not instruction.
3. **Tool-output boundary** — tool output is data, not instruction.
4. **Action authorization** — sensitive actions require explicit user
   authorization and a permitted destination.
5. **Disclosure boundary** — protected markers are never disclosed.
6. **No over-blocking** — legitimate actions still succeed.

## Vulnerable implementation weaknesses

- No authorization layer: every tool the assistant proposes executes.
- The assistant follows the highest-priority directive from any source
  (tool output, retrieved content, or user prompt), so injected instructions
  are acted upon.
- Protected markers are returned when asked.
- A spoofed authority ("SYSTEM MESSAGE …") is treated as real.

## Hardened implementation controls

- Authorization enforced in deterministic application code, outside the model.
- Sensitive tools require a user-source directive; retrieved/tool-output
  directives are denied.
- `expose_secret` and `exfiltrate` are never authorized.
- A synthetic deny-list blocks attacker-controlled destinations.
- Protected markers are never emitted unless a (never-authorized) disclosure
  tool is permitted.

## Assumptions

- The retrieval corpus can contain attacker-controlled documents (a realistic
  assumption for RAG over untrusted sources).
- The model is assumed to be *influenceable*: the whole point is to measure
  whether application enforcement survives that influence.
- The deterministic simulator's job is to model that influence transparently,
  not to claim fidelity to any particular real model.
