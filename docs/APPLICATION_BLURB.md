# Application-ready project descriptions

## Short

Responsible red-team assessment of a public Parker Solar Probe RAG chatbot. I
ran 505 structured evaluation jobs, found application-layer weaknesses in
conversation state, retrieval trust, metadata disclosure, scope enforcement,
and resource controls, disclosed them through NASA's VDP, and received a NASA
Letter of Recognition.

## Detailed

I red-teamed a third-party public RAG chatbot serving Parker Solar Probe
information. I designed a repeatable black-box evaluation spanning 505 scored
jobs and approximately 13 million reported tokens. Direct harmful-request
testing produced no automated-judge positives; important failures instead
appeared at system boundaries: conversation-state binding, retrieval
provenance, implementation-metadata disclosure, late scope checks, and token
amplification. I reported the findings responsibly through NASA's
Vulnerability Disclosure Policy and received a Letter of Recognition. This
case study publishes methodology, mitigations, synthetic data, and a minimal
offline analyzer while withholding replay details and third-party code.

## Interview framing

Lead with the engineering lesson, not "I jailbroke NASA": model refusal alone
did not secure the composed application. Stronger controls were required around
state, retrieval, provenance, scope, and budgets.
