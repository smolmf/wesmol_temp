from indexer.src.model.events.base import BaseEvent
from indexer.indexer.model.types import EvmAddress

class TransferEvent(BaseEvent):
    nft_address: EvmAddress
    nft_id: int
    from_address: EvmAddress
    to_address: EvmAddress