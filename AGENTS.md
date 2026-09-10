# PROJECT RULES — NON-NEGOTIABLE

1. CONTRACTS.md is frozen. Never change an endpoint path, request field,
   response field, or type. If a task seems to require it, STOP and ask.
2. Do NOT add dependencies. The approved list is in requirements.txt /
   package.json. Adding one requires explicit approval.
3. Do NOT create files outside the scope of the current task.
4. Do NOT refactor, rename, reformat, or "improve" any file you were not
   asked to modify. Working code is frozen code.
5. Do NOT add: auth, database, Docker, Celery, Redis, microservices,
   a /notify endpoint, LLM calls, or any cloud service.
6. services/features.py, loop_detector.py, rules.py, simulator.py are PURE.
   No I/O, no globals, no config reads, no logging. Ever.
7. Every task ends with: run the tests, show me the output. Never claim
   a test passes without pasting the output.
8. If a test fails, fix the code. Never delete, skip, or weaken a test.
9. No new abstractions. No base classes, no plugin systems, no factories.
   Concrete functions only.
10. When unsure, do the SIMPLER thing and say what you skipped.
