# Security policy

Report workflow-library vulnerabilities privately through GitHub Security
Advisories for `dinglebear-ai/workflows`.

High-impact findings include:

- a path that exposes secrets to fork or untrusted pull-request code;
- event/input expression injection into shell;
- a self-hosted release or untrusted job;
- a mutable external action or container reference;
- an unexpected permission elevation;
- publication that does not verify immutable release identity;
- publication of bytes other than those tested;
- bypass of the x86_64-only architecture contract.

Do not open a public issue containing a working secret-exfiltration or
publication-bypass proof.

