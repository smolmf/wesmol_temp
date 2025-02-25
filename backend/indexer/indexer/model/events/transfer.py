from .event import BaseEvent
from ..types import EvmAddress

class TransferEvent(BaseEvent):
    nft_address: EvmAddress
    nft_id: int
    from_address: EvmAddress
    to_address: EvmAddress