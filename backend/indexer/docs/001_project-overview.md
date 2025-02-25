# WESMOL Indexer Overview

## Architecture

The indexer consists of two main services:

1. **BlockDecoder Service**
   - Validates raw blocks from GCS
   - Decodes blocks into a standardized format
   - Stores both raw and decoded blocks
   - Tracks processing status in database

2. **EventIndexer Service** (future)
   - Consumes decoded blocks
   - Extracts and processes events
   - Stores data in database models
   - Builds domain-specific data model

## Component Structure

### Core Package (`indexer.indexer`)
- **contracts/** - Contract registry for decoding blocks
- **database/** - Database operations and models
- **decoders/** - Decoding classes
- **model/** - Data models and schemas
- **processing/** - Processing logic for blocks
- **storage/** - GCS storage operations
- **utils/** - Package utilities
- **env.py** - Environment configuration

### Config
- **abis/** - ABIs for decoding
- **contracts.json** - Contract registry config

### Setup

### Services
- **services/processor/** - BlockProcessor Cloud Run service
- **services/indexer/** - EventIndexer Cloud Run service (future)

### Scripts
- **scripts/reprocess.py** - For reprocessing failed blocks
- **scripts/fix_block.py** - For manual fixes to blocks

## Data Flow
1. Raw blocks arrive in GCS bucket via external service
2. Pub/Sub notification triggers BlockProcessor
3. BlockProcessor validates, decodes, and stores decoded blocks
4. Successfully decoded blocks trigger EventIndexer (future)
5. EventIndexer processes events and updates database (future)

## Environment Setup
- Uses environment variables for configuration
- Supports both local development and cloud deployment
- Database connection managed via PostgreSQL