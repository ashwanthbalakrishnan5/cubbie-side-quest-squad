# Decisions made during the build

One line each: what was decided, and why, when the plan didn't cover it.

- `LLMError` lives in `squad/llm.py` from Task 0 so `tests/fakes.py` can import it; Task 4 adds `LLM` to the same file.
- WhatsApp pairing is skipped for now (user choice 2026-10-25): `wa-voice` is built and tested, nudges use DMs until paired.
- Track 3 submission is held until the user records the demo video.
