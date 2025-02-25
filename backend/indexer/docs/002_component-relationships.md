# Component Relationships

## BlockDecoder Service

### Core Components

1. **BlockValidator**
   - Validates raw blocks against the `EvmFilteredBlock` schema
   - Uses msgspec for schema validation
   - Returns validation status and decoded block

2. **BlockDecoder**
   - Transforms validated blocks into standardized format
   - Extracts transactions, events, and other data
   - Prepares data for storage

3. **BlockHandler**
   - Handles storage of raw and decoded blocks
   - Manages GCS paths and prefixes
   - Provides methods to store and retrieve blocks

4. **BlockProcessor** (main orchestrator)
   - Coordinates the validation -> transformation -> storage process
   - Tracks processing status in database
   - Handles errors and reprocessing

### Database Components

1. **ConnectionManager**
   - Provides database session management
   - Initializes database connection
   - Creates tables if needed

2. **DatabaseManager** (DB operations)
   - Records block processing status
   - Updates validation errors
   - Queries block processing status

3. **ProcessingStatus** (Enum)
   - PENDING
   - PROCESSING
   - VALID
   - INVALID

4. **BlockProcess** (DB model)
   - Stores validation status of blocks
   - Tracks errors and timestamps
   - Relates to block number and GCS path

### Storage Components

1. **GCSBaseHandler**
   - Low-level GCS operations
   - Uploads and downloads blobs
   - Tracks blob versions and changes

## Key Relationships

- **BlockProcessor** uses **BlockValidator**, **BlockDecoder**, and **BlockHandler**
- **BlockProcessor** stores status in database via **DatabaseManager** (DB operations)
- **BlockHandler** uses **GCSBaseHandler** for GCS operations