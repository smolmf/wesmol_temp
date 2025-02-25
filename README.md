# wesmol

stream: filtered data stream from RPC to raw data storage
indexer: data processing
website: frontend



"""
Process:
Raw EVM Logs -> Decoded EVM Logs Mapped to Indexer Structure (Log Decoding) 
Decoded Logs -> Standardized Events (Contract Mapping)

Event Decoders:
- The topic0 hash (& name) is deterministic for each event signature
- However, multiple event signatures may share a topic0 hash
- Event decoders are associated with an event signature and produce a dict of log attributes

"""

how to use

# Deploy to Cloud Run
make deploy

# Reprocess blocks
make reprocess start=1234567 end=1234670 contracts=0x123,0x456

# Add new contract
make add-contract address=0x789 abi=./abis/new_contract.json start=1234567




# LATEST: HOW TO RUN DEVELOPMENT SCRIPTS (IE INDEXER/SCRIPTS)

## Navigate to the indexer directory
cd wesmol/backend/indexer
## Run a script
python scripts/sync_gcs.py

## Key points:
* Always run from the indexer directory
* Scripts add src to Python path at runtime
* Environment variables are loaded in a specific order
* Paths are resolved relative to the env.py location
* Common paths are available via the paths dictionary

## If need to import indexer code from elsewhere:
[python]
import sys
from pathlib import Path
indexer_src = Path("/path/to/wesmol/backend/indexer/src")
sys.path.append(str(indexer_src))
from env import paths
'# Now you can import other indexer modules