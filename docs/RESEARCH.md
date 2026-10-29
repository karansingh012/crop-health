# Reproducible research workflow

## Current evidence

A transfer-learning CNN–ViT hybrid has now been trained for 10 epochs on a reproducibly sampled PlantVillage pilot (100 candidate images per class). 3,795 images remain after duplicate/ambiguity exclusions, split into 3,035 training, 376 validation and 384 test images across 38 classes. The validation-selected epoch achieved 81.77% internal test accuracy and 0.8153 macro-F1. This is a limited controlled-image experiment, not evidence of field reliability. See MODEL_CARD.md and the actual JSON outputs in verification/pilot. PlantDoc external evaluation and full-data comparisons remain pending. Earlier synthetic runs remain clearly separated under verification/synthetic-pipeline.

## Obtain datasets

Primary sources:

- PlantVillage: https://github.com/spMohanty/PlantVillage-Dataset and https://arxiv.org/abs/1511.08060
- PlantDoc: https://github.com/pratikkayal/PlantDoc-Dataset and https://arxiv.org/abs/1911.10317

Review dataset licenses, redistribution restrictions and annotation quality before use. Download manually or clone the repositories into `datasets/`. PlantVillage's `raw/color` directory has the supported class-folder form. Do not combine color/segmented/grayscale versions as independent images. For PlantDoc use the classification image folders, not bounding-box CSVs as if they were image labels. Do not change official splits without documenting the protocol.

Example acquisition commands (large downloads; confirm available disk and licensing first):

```sh
mkdir -p datasets
git clone --depth 1 https://github.com/spMohanty/PlantVillage-Dataset.git datasets/PlantVillage-Dataset
git clone --depth 1 https://github.com/pratikkayal/PlantDoc-Dataset.git datasets/PlantDoc-Dataset
```

If a repository uses Git LFS, install Git LFS and fetch its objects before preparation. The decoding audit rejects non-image pointer files. Inspect the resulting directories and labels rather than assuming an image count.

Required structure:

```
datasets/plantvillage/
  Tomato___healthy/image1.jpg
  Tomato___Early_blight/image2.jpg
  ...
```

Only direct files inside direct class folders are ingested. Images are decoded and class counts, invalid files, pixel hashes, perceptual hashes, removals and split counts are written to the manifest.

```sh
python -m ml.prepare datasets/PlantVillage-Dataset/raw/color datasets/plantvillage.json --seed 42
```

Preparation deterministically keeps one representative of pixel-exact or pHash Hamming-distance <=4 duplicates before stratified splitting. Conflicting duplicate labels stop the run by default. The explicit `--quarantine-conflicts` option removes both matched representatives and conflicting images before splitting and records the exclusions; the pilot used this conservative option. Every retained class needs at least 10 images. Ratios are 80/10/10 up to integer rounding, with the remainder assigned to test. Do not manually tune duplicate criteria using test results. Near-duplicate detection is heuristic; inspect removal logs and additionally group by source plant/photograph where such metadata is available. Source-plant grouping is not implemented, so undetected correlated images remain a leakage risk.

## Architecture

All models accept normalized RGB 128 x 128 images. Normalization uses ImageNet mean/std for a consistent documented convention; the default weights are trained from scratch, not ImageNet-pretrained.

- CNN: 3->24 stride-2 convolution; 24->D stride-2 convolution; depthwise stride-2 convolution and pointwise D->D; global average pooling -> D.
- ViT: nonoverlapping 16x16 patch embedding -> 64 tokens of width D; learned positional embeddings; four-head Transformer encoder; mean token pooling and LayerNorm -> D.
- Hybrid: parallel CNN and ViT; concatenate D+D features, project 2D->D with GELU/dropout, classify D->K.
- Full CNN/ViT/hybrid use D=96, four Transformer layers when present.
- Lightweight uses D=48 and two Transformer layers, with the same explicit fusion.
- Optimized is the lightweight architecture with 30% L1 unstructured pruning on convolution weights, masks retained during training and removed when saving. This does not shrink dense tensors or promise speedups. Measure its accuracy/storage/latency before claiming a benefit.

All components are differentiable. `--initialize` optionally loads an earlier compatible checkpoint for continued training; the additional `transfer_hybrid --pretrained` variant initializes a MobileNetV3-small feature extractor using torchvision ImageNet weights. That explicit flag downloads the official weight file. It freezes CNN weights while training the local projection, patch Transformer and fusion head; batch-normalization running statistics adapt on training batches. CNN output 576 is projected to 48, concatenated with the 48-dimensional Transformer representation and classified. Inference rebuilds the architecture without downloading weights.

## Train and select

```sh
for model in cnn vit hybrid lightweight optimized; do
  python -m ml.train datasets/plantvillage.json --model "$model" \
    --output "experiments/$model" --epochs 20 --batch-size 32 --seed 42
done
```

Record dataset version, downloaded path, hardware, command and manifest hash. Training uses AdamW, cross-entropy, horizontal flip, rotation and color jitter on training only. Seeded sampling, Python/NumPy/PyTorch seeds and deterministic-algorithm warnings are enabled. CUDA is used if available, CPU otherwise. Apple MPS is not used. Validation macro-F1 chooses the saved epoch. Histories, train/validation loss and F1 plots, configuration and checkpoint are written per run. Repeat across seeds for statistical comparisons; exact cross-hardware bitwise reproducibility is not guaranteed.

Choose architecture/hyperparameters using validation only. Then select an empirical abstention threshold:

```sh
python -m ml.evaluate datasets/plantvillage.json experiments/lightweight/best.pt \
  --split val --select-threshold --output experiments/lightweight/validation
```

This chooses maximum validation coverage subject to >=90% empirical accepted accuracy and at least 20 accepted examples. If the criterion is not met, threshold stays null and all application outputs remain uncertain. This is not calibration and does not provide a confidence bound. The evaluator requires the original manifest hash for threshold selection. Never select on internal test or PlantDoc. Keep an untouched test set to assess the selected threshold's practical behavior; selective risk/coverage curves and temperature scaling are future extensions.

## Internal evaluation

```sh
python -m ml.evaluate datasets/plantvillage.json experiments/lightweight/best.pt \
  --split test --output experiments/lightweight/internal-test
python -m ml.report experiments --output experiments/comparison
```

Outputs: accuracy, per-class precision/recall/F1/support, macro-F1, confusion matrix JSON/PNG, misclassified filenames/classes/scores, parameter count, checkpoint bytes, batch-1 CPU median/p95 latency, throughput and sampled process RSS. Five warmup passes precede measurements. Timing excludes preprocessing and data loading, and includes model forward plus softmax. RSS is sampled process memory, not isolated model allocation or a true continuous peak. Hardware/runtime/thread count are recorded. No GPU timing is claimed. Comparison CSV/Markdown reads actual JSON outputs only; absent experiments remain pending.

## External evaluation

Create a reviewed JSON mapping from actual PlantDoc folder names to exact PlantVillage labels. Do not automatically equate similarly named disease classes. Example mapping shape (verify actual class names before use):

```json
{"tomato leaf":"Tomato___healthy","tomato early blight leaf":"Tomato___Early_blight"}
```

```sh
python -m ml.external datasets/PlantDoc-Dataset/test datasets/plantdoc-map.json \
  datasets/plantvillage.json datasets/plantdoc-external.json
python -m ml.evaluate datasets/plantdoc-external.json experiments/lightweight/best.pt \
  --split external --output experiments/lightweight/plantdoc
```

Unmapped labels and potential pHash overlap with any development image are excluded and logged. The classifier keeps its full output head; unsupported predictions count as errors. Report coverage and the compatible subset, not a misleading score across untested classes. External data must never set thresholds, select epochs or tune architecture.

## Deployment checkpoint

After reviewing real evaluation results:

```sh
mkdir -p models
cp experiments/lightweight/best.pt models/selected.pt
docker compose restart backend
```

The architecture name, ordered classes, normalization, threshold and trusted state dictionary travel with the checkpoint. CPU is the serving default. Benchmark the actual checkpoint on the intended machine before choosing infrastructure size.

## Guidance sources and limits

Early-blight entries are brief paraphrases from UMN Extension: https://extension.umn.edu/agriculture/specialty-crops/vegetable-farming/disease-management/early-blight-in-tomato-and-potato . Only tomato and potato early blight receive these entries. General entries explicitly say disease-specific advice is unavailable. No chemical dosages are provided. Local validation and expert review are required before expanding the catalog.

Weather uses Open-Meteo documented current variables: https://open-meteo.com/en/docs . High humidity is contextual information, not proof of leaf wetness or disease. The current risk service does not model disease progression, incorporate historical weather, or compute a validated risk index.

## Reproduce the installed pilot

```sh
python ml/download_pilot.py
python -m ml.prepare datasets/plantvillage-pilot datasets/pilot-manifest.json --seed 42 --quarantine-conflicts
# Set training_scope="plantvillage_pilot" in the manifest for the research-preview notice.
python -m ml.train datasets/pilot-manifest.json --model transfer_hybrid --pretrained --epochs 10 --batch-size 32 --threads 4 --lr 0.001 --output experiments/pilot
python -m ml.evaluate datasets/pilot-manifest.json experiments/pilot/best.pt --split val --select-threshold --output experiments/pilot/validation
python -m ml.evaluate datasets/pilot-manifest.json experiments/pilot/best.pt --split test --output experiments/pilot/test
```

The original acquisition list and complete retained-image manifest are stored with the verification evidence. Source-plant grouping is still not implemented; perceptual duplicate removal cannot eliminate every correlated image. Do not present the internal test as an independent field trial.
