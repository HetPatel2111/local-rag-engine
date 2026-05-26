# Evaluation Report

## Summary
- top1 relevance: 0.7423
- false positives: 0
- avg confidence: 0.6873
- avg latency ms: 173.78

## Confidence Distribution
- high: 0
- medium: 3
- low: 2

## Query Results
| query | expected | found | confidence | latency_ms | sources |
|---|---:|---:|---:|---:|---|
| What is Vite? | true | true | 0.7417 | 219.98 | https://vite.dev/guide/, https://vite.dev/guide/why, https://vite.dev/config/shared-options, https://vite.dev/plugins/ |
| What is HMR? | true | true | 0.6878 | 74.36 | https://vite.dev/guide/api-hmr, https://vite.dev/guide/api-plugin, https://vite.dev/guide/api-environment-plugins |
| Why is Vite fast? | true | true | 0.7582 | 92.91 | https://vite.dev/guide/performance, https://vite.dev/guide/, https://vite.dev/guide/why, https://vite.dev/guide/philosophy |
| How do env variables work? | true | true | 0.7813 | 397.07 | https://vite.dev/guide/env-and-mode, https://vite.dev/config/ |
| What is the capital of France? | false | false | 0.4675 | 84.60 | - |

## Notes
- The out-of-domain query should remain unanswered.
- Confidence is used as a refusal gate, not as a generative guarantee.
