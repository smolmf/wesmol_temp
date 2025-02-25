from typing import Literal, Optional
from indexer.indexer.model.events.event import BaseEvent
from indexer.indexer.model.types import EvmAddress

class TradeEvent(BaseEvent):
    contract: Optional[EvmAddress]
    sender: Optional[EvmAddress]
    direction: Literal["buy","sell"]
    buyer: EvmAddress
    seller: EvmAddress
    nft_address: EvmAddress
    nft_id: int
    token_address: str
    price: int