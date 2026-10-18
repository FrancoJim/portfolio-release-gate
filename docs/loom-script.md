# Three-minute Loom — verified local demo

Before recording, follow the README startup commands. Open http://127.0.0.1:8000, the local architecture diagram, handler, local adapter, and successful CI run. Run `python3 scripts/smoke.py http://127.0.0.1:8000` and keep its output available. KJ records the Loom. Hide unrelated windows and credentials.

**0:00–0:25 — outcome and local URL**

“This is Release Gate, a local portfolio demo of a release-readiness checklist. It runs on this computer using Python's standard library, without cloud credentials or paid services. It checks four release controls and identifies what is missing.”

**0:25–0:55 — browser interaction**

Leave rollback unchecked and submit. “The API identifies rollback as missing.” Check all four and submit. “The checklist is ready for review. This is a demo result, not production release approval. Submissions are not stored.”

**0:55–1:25 — README diagram and source**

“The browser talks to a server bound only to 127.0.0.1. A small HTTP adapter calls the shared Python handler, which serves the interface and calculates the result. There is no database or external service. Another engineer can reproduce this from the README with no package installation.”

**1:25–2:00 — verification**

Show successful smoke output and unit tests. “The HTTP smoke checks cover the homepage, health, all checks passing, missing rollback, and invalid input. Unit and HTTP integration tests cover request validation and routing. GitHub Actions also checks JavaScript syntax and validates the retained Terraform examples without cloud credentials.” Only show a CI run confirmed successful for this change.

**2:00–2:30 — boundaries and recovery**

“The AWS files are optional, unexecuted reference examples. This demo does not claim a cloud deployment. To stop it, press Ctrl-C. To repeat it, run the same startup command. A Git revert can restore a previous version; there is no submitted data or cloud state to migrate for the local app.”

**2:30–3:00 — handoff**

“The repository includes exact startup commands, a local architecture diagram, automated checks, and clear limits. For client work, I would agree on the controls, verification evidence, approver, and recovery steps before release.”
