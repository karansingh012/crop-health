# Installed research-preview model

Date: 29 October 2026. Architecture: `transfer_hybrid`. Artifact: `models/selected.pt`.
SHA-256: `fdf93638a047348fa62f95c9c1e19693c4cafbe8f89629957258ce087ca0c568`.

## Real training data and protocol

PlantVillage color images, sampled deterministically with seed 42: 100 candidates per each of 38 classes, 3,800 images downloaded. After one within-class duplicate and two ambiguous cross-label pairs were excluded, 3795 images remained: 3035 train, 376 validation, 384 internal test. Ambiguity quarantine was performed before the split. The acquisition list, source tree revision, retained image hashes, split assignments and exclusions are in verification/pilot.

The model uses ImageNet MobileNetV3-small CNN features (576 -> 48 projection) concatenated with a two-layer, width-48 patch Transformer branch. The 96-dimensional fused vector feeds a learned classification head. CNN parameters are frozen; their batch-normalization running statistics adapt during training. Transformer, projection and classifier parameters are trained. Input is RGB 128x128 with documented ImageNet normalization and training-only augmentation.

10 epochs, CPU, AdamW, learning rate 0.001, batch 32, seed 42. Epoch 9 was selected by validation macro-F1. No test images selected epochs or thresholds. Raw softmax scores remain **uncalibrated**.

## Measured internal results

| Metric | Result |
|---|---|
| Test images | 384 |
| Accuracy | 81.77% |
| Macro-F1 | 0.8153 |
| Macro precision | 0.8376 |
| Macro recall | 0.8167 |
| Parameters | 1,048,534 |
| Saved checkpoint | 4.32 MB |
| CPU median inference | 29.66 ms |
| CPU p95 inference | 45.76 ms |

Timing is a batch-one local CPU observation with four threads, after warmup, excluding image preprocessing. See metrics.json for hardware/runtime and sampled process RSS; it is not a target-server capacity guarantee.

Validation selected threshold 0.54 for >=90% empirical accepted accuracy with at least 20 retained examples. Untouched-test selective results: `{"threshold": 0.54, "accepted_count": 299, "coverage": 0.7786458333333334, "accepted_accuracy": 0.9063545150501672}`. These are model-only selection metrics; serving also abstains on basic image-quality warnings. A score above the threshold is still only a possible class match.

## Important boundaries

This is a small balanced subset of controlled PlantVillage photographs, not the full dataset. pHash deduplication is heuristic; no source-plant grouping or independent PlantDoc/field validation was performed. Unsupported crops, nutrient problems and non-plant images can receive incorrect high scores. A healthy-class match does not prove plant health. Do not extrapolate this internal accuracy to photographs captured on farms.

The application labels every result as a research preview and offers expert support and reanalysis. Existing scans retain their original report; reanalysis creates a new owned record. This release resolves missing model weights without fabricating predictions or reusing synthetic checkpoints.

Sources: [PlantVillage repository](https://github.com/spMohanty/PlantVillage-Dataset), [dataset paper](https://arxiv.org/abs/1511.08060), [torchvision MobileNetV3 weights](https://docs.pytorch.org/vision/stable/models/generated/torchvision.models.mobilenet_v3_small.html). The exact official initialization file was `mobilenet_v3_small-047dcff4.pth`. Review upstream data terms before commercial reuse. No dataset is included in the source ZIP.
