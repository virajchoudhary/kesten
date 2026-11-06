# Diagnostic-script discovery failure

On 2026-11-05, `.venv/Scripts/python.exe -m unittest discover -s tests -p 'test_*.py'` ran 10 discovered entries with 7 import errors.

`test_backtest.py`, `test_bt_dump.py`, `test_opt.py`, `test_opt_dump.py`, `test_opt_json.py`, and `test_req.py` issue legacy HTTP requests at module import. The sandbox denied those connections. These scripts have no unittest assertions and target the old unauthenticated port-8000 API contract. `test_out.py` reads absent `out.txt` at import and raised `FileNotFoundError`.

The scripts remain unchanged for research traceability. They are not accepted regression coverage. CI selects `test_research_client.py` and `test_dev_environment.py` explicitly, alongside Django and frontend tests. A future research-test cleanup should convert the diagnostics into opt-in CLI commands with authenticated requests, bounded timeouts, and assertions where appropriate. Do not run generic discovery with unrestricted provider/network access.
