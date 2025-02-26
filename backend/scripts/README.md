# REPROCESS.PY

Can run the reprocess script in different ways:

## 1. Reprocess all invalid blocks via the API:

```bash
python backend/scripts/reprocess.py --all-invalid --api-url https://your-processor-service-url
```

## 2. Reprocess specific blocks directly (without the API):

```bash
python backend/scripts/reprocess.py --mode direct --blocks 12345 12346 12347
```

## 3. Reprocess blocks from a file:

```bash
python backend/scripts/reprocess.py --file blocks_to_fix.txt
```


# FIX_BLOCK.PY

This script provides three key functions:

## 1. Examine blocks to see what's wrong:

```bash
python backend/scripts/fix_block.py examine 12345
```

## 2. Patch blocks with manual fixes:

```bash
python backend/scripts/fix_block.py patch 12345 my_fix.json
```

## 3. Reset block status to force reprocessing:

```bash
python backend/scripts/fix_block.py reset 12345
```

# BATCH PROCESSOR

```bash
# Sample 5 blocks and store locally
python backend/scripts/batch_processor.py --sample 5 --storage local --local-db 

# Process specific blocks and store in GCS
python scripts/batch_processor.py --block-numbers 12345 12346 12347 --storage gcs

# Process invalid blocks and store locally
python scripts/batch_processor.py --status invalid --limit 50 --storage local

# Process blocks from a file
python scripts/batch_processor.py --file block_list.txt --storage local
```