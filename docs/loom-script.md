# Three-minute Loom — one-take script

Before recording, open the README diagram, app handler, Terraform, CI run, and deploy run. If a real deployment is not verified, record a source walkthrough and say so; do not call it a live demo. Once verified, open its URL and keep the successful smoke-test step visible. Hide account details and credentials.

**0:00–0:25 — outcome, README**

“This is Release Gate, a small portfolio app that shows a complete delivery path: application checks, infrastructure as code, and a controlled cloud release. The app checks four release controls. The main point is that another engineer can understand how it gets deployed and how to recover it.”

**0:25–0:55 — app, after deployment only**

“I’ll leave rollback unchecked and submit. The API identifies the missing control. When all four are checked, it says the checklist is ready for review. This is a demo, not an automatic production approval. Submissions are not stored.”

If deployment is pending, replace that paragraph with: “The interface and API are built and tested. Cloud deployment is still pending account setup, so I’m showing the source and test evidence rather than claiming a live service.”

**0:55–1:25 — diagram and Terraform**

“API Gateway accepts HTTPS and invokes a Python Lambda. Terraform defines the app archive, runtime role, logs, gateway, and invocation permission. The runtime can write its own logs. There is no database or cluster to maintain for this example. Log retention and gateway throttling are explicit.”

**1:25–2:00 — GitHub Actions**

“Pull requests run application tests and Terraform validation without cloud credentials. Deployment is a separate manual workflow restricted to main, using the demo environment. GitHub OIDC supplies temporary AWS credentials. State is encrypted in S3 with locking. The workflow creates a plan, applies that saved plan, then checks the live homepage, health endpoint, and API result.”

**2:00–2:30 — tests and recovery**

“The tests cover valid checks, incomplete checks, invalid input, request size, encoding, and routes. A failed smoke test fails the release job. Recovery is explicit: revert the application change and redeploy, or inspect an infrastructure failure while preserving state. This sample does not claim automatic rollback.”

**2:30–3:00 — handoff**

“The README explains setup, tradeoffs, teardown, and the limits of the demo. For a client, I’d start with the same questions: what must change, how do we prove it works, who approves the release, and how do we reverse it? That keeps a small delivery useful after the handoff.”
