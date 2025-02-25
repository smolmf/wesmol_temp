from msgspec import Struct

class BaseEvent(Struct):
    timestamp: datetime
    tx_hash: EvmHash
