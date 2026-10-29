# Current implementation status

Updated 29 October 2026 (Asia/Kolkata).

## This upgrade

- A real MobileNetV3 + ViT hybrid checkpoint is installed at `models/selected.pt`; no external image-classification API or synthetic weights are used.
- Persistent Hindi/English selection covers navigation, forms, result/guidance text, dates, accessible labels, errors and downloadable reports. User names and notes stay unchanged.
- Weather uses city/village/postal-code search with explicit region/country choices, or an optional browser location request. Coordinate inputs have been removed. Location permission denial falls back to search.
- Saved images can be reassessed into a new owned scan without overwriting the original record/report.
- Very poor contrast/lighting causes abstention without a disease class or score. Missing/invalid weights still fail honestly.

## Executed verification

- 16 backend/model tests pass, including authentication/ownership, image validation, weather failures, place search/validation, reanalysis protection and Hindi PDF generation. One upstream Starlette/httpx test-client deprecation warning remains.
- Frontend production build succeeds.
- All 3 browser tests pass (12.8 seconds). They cover the original workflow plus Hindi persistence across routes/reload, real place-name weather, device location/denied permission, Hindi PDF downloads, theme and mobile overflow.
- The live Compose API produced real model output on an internal-test image, returned a Hindi report, preserved the original after reanalysis and retrieved real weather after named-place lookup. See `verification/model-and-location-integration.json`.
- Hindi desktop/mobile screenshots and rendered PDF pages were visually checked. Embedded Noto fonts and HarfBuzz prevent missing Devanagari glyphs.
- PostgreSQL, images and original records remain in the existing volumes. No database reset was performed. The earlier restart-persistence evidence remains under verification.

## Real pilot experiment

3,800 PlantVillage images were downloaded (100 candidates per each of 38 classes). One same-class duplicate and two ambiguous cross-label pairs were excluded before splitting. The retained 3,795 images comprise 3,035 training, 376 validation and 384 internal test samples. Ten epochs were completed; validation selected epoch 9.

Internal test accuracy: **81.77%**. Macro-F1: **0.8153**. Validation-selected abstention threshold: **0.54**, with uncalibrated softmax scores. On untouched internal test data, 299/384 predictions exceeded the threshold and 90.64% of those were correct. This is a controlled-image subset result, not field reliability. Full provenance, metrics, confusion matrix and limitations are in MODEL_CARD.md and verification/pilot.

## Remaining limits

The full PlantVillage experiments and independent PlantDoc/field evaluation remain unfinished. The original five architecture pipelines and their synthetic smoke evidence are retained separately. Source-plant grouping, validated OOD detection and probability calibration remain unavailable. Disease-specific guidance covers tomato/potato early blight; other classes receive general advice. Follow-ups remain in-app records, expert sharing is explicit email composition, and account recovery/verification is not implemented. Private local-volume storage is single-host; scaling needs a storage adapter/shared filesystem and distributed rate limiting. AWS deployment and target-host benchmarking have not been performed.
