# DEVELOPMENT STAGES AND COMPONENTS

## 1. Validation & Storage Stage

* Set up Pub/Sub trigger from GCS
* Validate block format
* Store valid/invalid status
* Store raw blocks in organized GCS structure
### Goal: Ensure reliable block ingestion and validation


## 2. Decoder Stage

* Implement block decoder
* Store decoded blocks in GCS
* Track decoder versions
* Enable reprocessing capability
### Goal: Reliable block decoding with version control


## 3. Database Design & Initial Load

* Design schema for blocks, transactions, events
* Set up Cloud SQL
* Implement basic data loading
* Set up test queries
### Goal: Verify database design works for real data


## 4. Mapper & Indexing Stage

* Implement mappers for your data model
* Store mapped data in database
* Track mapper versions
* Enable selective reprocessing
### Goal: Complete data transformation pipeline


## 5. Operational Stage

* Implement monitoring
* Add error handling
* Set up reprocessing tools
* Add performance tracking
### Goal: Production-ready system







Indexer - OLD README

Handles processing from FilteredBlock JSON in S3 bucket (raw) to Database / Storage (processed)

Elements:
- Logs Templated
- Contracts mapped to Logs and Events
- Records produced from Logs at TX level
- Data Model
- Database Interfacing
- Scripts available for CLI and Worker Processes

Key principles:

Models: Focus on runtime data processing, validation, transformations
Schema: Handle persistence, indexing, relationships
Use mapper functions to convert between models and schema
Keep models independent of database implementation


To generate requirements.txt from your virtual environment, you can use:

[bash]
pip freeze > requirements.txt

To generate requirements.txt from your virtual environment, you can use:

[bash]
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt