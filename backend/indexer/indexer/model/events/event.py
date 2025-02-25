from msgspec import Struct
from datetime import datetime
from indexer.indexer.model.types import EvmHash

class BaseEvent(Struct):
    timestamp: datetime
    tx_hash: EvmHash
