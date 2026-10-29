# Demonstration, troubleshooting and viva

## Demonstration

1. Start Compose and register a new account. Point out that dashboard counts reflect this account's records, not seed data.
2. Create a field with crop, hectares and optional location; edit it and inspect history.
3. Upload a JPEG/PNG/WebP leaf photograph with notes. When weights are missing the observation is saved and the UI says model unavailable. It must not invent a label.
4. Download the private PDF; inspect image, timestamp, notes and limitations.
5. Schedule a follow-up, mark it complete, then reopen the original observation.
6. Save a second observation and select both in history. Discuss why differences do not prove progression.
7. Fetch weather by city/village name, select the matching region, or explicitly choose Use my location. Show timestamp, units and provider attribution. Disable the provider to demonstrate graceful failure.
8. Open Expert support. Without configured contact it explains the missing setup. With contact it opens an email draft; users decide what to attach.
9. Sign out; protected routes return to login. A second account cannot see the first user's fields, images or reports.
10. Explain the separate research pipeline and its actual status. The installed pilot has real internal metrics; do not present them as field reliability or confuse them with the earlier synthetic pipeline tests.

## Troubleshooting

| Symptom | Check |
|---|---|
| Compose cannot interpolate password | Create `.env` from example and use a URL-safe secret. |
| Port 8080 in use | Stop the conflicting service or change the host port and CORS origin. |
| API unavailable | `docker compose ps` and `docker compose logs --tail=100 backend migrate db`. |
| Migration fails | Confirm DATABASE_URL, DB credentials, health and existing migration history. Do not delete volumes as a first fix. |
| Images fail validation | JPEG/PNG/WebP, <=8 MB, >=64 pixels per dimension, valid decoded data and <=20M pixels. |
| No prediction | Install a trusted real checkpoint as `models/selected.pt` and restart backend. Development-only checkpoints are rejected. |
| All predictions uncertain | Expected without validation threshold, below threshold or poor quality. Run validation selection; do not relax policy using test data. |
| Weather unavailable | Check internet access, provider availability, WEATHER_ENABLED and customer key if used. Free noncommercial endpoint needs no key. |
| Report image missing after host move | Restore the private upload volume as well as the DB. |
| 401 response | Session expired or revoked. Sign in again. |
| 429 response | Respect Retry-After; use a distributed/edge limiter for scaled deployment. |
| Browser tests cannot launch | Run `npx playwright install chromium`; use installed browser dependencies for your OS. |
| Model memory too high | Reduce training batch size, use lightweight architecture, measure actual serving RSS and CPU concurrency. |

## Viva notes

**Why CNN?** Convolution learns local patterns with spatial weight sharing, useful for lesion texture, borders and color patterns. This is a hypothesis to test, not proof that a given symptom is diagnostic.

**Why ViT?** Self-attention models relationships among image patches. This implementation learns embeddings for 64 patches and uses Transformer layers; data efficiency and generalization must be measured.

**How are branches fused?** Both output D-dimensional vectors. Concatenation forms 2D, followed by learned projection/GELU/dropout and a K-class linear head. Dimension flow is explicitly tested.

**What makes the lightweight variant smaller?** Width falls from 96 to 48 and Transformer depth from four to two. Parameter count and actual latency are measured separately because fewer parameters do not always mean faster hardware execution.

**What is transfer learning?** Reusing representations trained on another task. This implementation trains from scratch by default and supports compatible checkpoint initialization, but now includes a real pilot experiment using frozen ImageNet MobileNetV3 features fused with a trainable ViT branch. See MODEL_CARD.md.

**Why an external dataset?** Controlled backgrounds may hide domain-shift problems. PlantDoc evaluation on explicitly compatible labels tests a different distribution, but cannot establish universal field reliability.

**What prevents leakage?** Deduplicate before splitting; preserve the manifest and seed; use training augmentations only on train; choose epochs/thresholds on validation; keep internal/external tests untouched. pHash is imperfect and source-plant grouping remains a limitation.

**What is macro-F1?** The arithmetic mean of per-class F1 values, giving each class equal weight. Precision assesses correctness of positive predictions; recall assesses recovered true examples. Confusion matrices expose class-specific mistakes.

**Is 90% softmax a 90% probability of disease?** No. Softmax is a relative model score. Calibration requires held-out evidence and metrics. Here only an empirical validation abstention threshold is selected; no calibrated probability claim is made.

**How is uncertainty handled?** Low score, missing threshold or poor quality marks the result uncertain. Missing weights produces no prediction. Unsupported inputs are not reliably detected, even at high score.

**What does pruning do?** It zeros selected convolution weights. Dense tensor storage/runtime may not improve; the code does not claim compression or speedup until measured.

**How is latency measured?** CPU batch one after five warmups, forward and softmax timed, preprocessing excluded; median/p95, throughput, observed RSS and runtime/hardware are recorded. End-to-end HTTP latency is a different metric.

**How are records protected?** Password hashes, expiring server-side bearer sessions, ownership checks on all private resources, non-public storage and a TLS reverse proxy in production. Authentication and authorization are distinct controls.

**Why not call weather a diagnosis?** Weather can favor environmental conditions, but cannot demonstrate a pathogen's presence. The engine returns context, not a validated numerical disease-risk index.

**What remains before deployment?** Real dataset/label review, supervised training, external evaluation, checkpoint validation, target-host benchmarking, broader guidance review, approved infrastructure and tested cloud backup/restore.
