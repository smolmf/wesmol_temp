from typing import Literal, Optional
from indexer.indexer.model.events.event import BaseEvent
from indexer.indexer.model.types import EvmAddress

class MintEvent(BaseEvent):
    contract: Optional[EvmAddress]
    sender: Optional[EvmAddress]
    minter: EvmAddress
    nft_address: EvmAddress
    nft_id: int
    token_address: str
    price: int