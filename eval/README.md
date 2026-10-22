# Evaluation reports

Every lane writes measured results to `eval/reports/<lane>_<name>.json` as a JSON list of records:

```json
[{"lane": "ml", "metric": "macro_f1", "value": 0.81, "n": 152, "split": "test",
  "notes": "ensemble, calibrated", "created": "2026-10-23T22:10:00-05:00"}]
```

They feed `/api/metrics` (the Transparency page) and the README tables. Report real numbers only, including n and the split.
