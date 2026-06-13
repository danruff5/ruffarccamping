# Image Similarity Filtering Design

This document details the design for introducing Perceptual Hashing (dHash) to filter visually similar duplicate images in the static site gallery and select the highest-rated image from each matching sequence.

## User Review Required

> [!NOTE]
> Database schema migration is handled automatically at startup. For existing images already in `Done` status, a background migration will calculate their `dhash` value on-the-fly and update the database.

## Proposed Changes

### 1. Database Schema Update
- Add a new column `dhash TEXT` to the `images` table in [db.py](file:///c:/Users/dckra/Desktop/ruffarc/backend/db.py).
- Update the startup database migration helper to add this column.
- Automatically calculate `dhash` for all existing `Done` rows where `dhash IS NULL`.

### 2. Hash Calculation & Comparison Utility
- Implement a pure Python `dhash` calculator using Pillow.
- Grayscale conversion, resizing to 9x8, and bit difference calculation.
- Implement a `hamming_distance(h1, h2)` function.

### 3. Background Worker Update
- Modify `process_single_image` in [worker.py](file:///c:/Users/dckra/Desktop/ruffarc/backend/worker.py) to calculate the `dhash` value of the photo and store it.

### 4. Static Site Builder Selection Update
- Modify `filter_and_group_images` in [build_site.py](file:///c:/Users/dckra/Desktop/ruffarc/build_site.py) to run the **Streaming Leader-Election** algorithm:
  - If a photo is similar to the current leader ($\text{Hamming distance} \le 10$), choose the one with the higher `score`.
  - Fall back to comparing description similarity using `SequenceMatcher` if either photo lacks a `dhash`.

## Verification Plan

### Automated Tests
- Add a test suite verifying `calculate_dhash` output correctness.
- Add a test suite verifying that `filter_and_group_images` correctly groups similar hashes and selects the highest scoring photo.
- Verify migration script successfully populates `dhash` values.
