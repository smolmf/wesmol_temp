from typing import Literal, Optional

from .event import BaseEvent
from ..types import EvmAddress

class UpgradeEvent(BaseEvent):
    contract: Optional[EvmAddress]
    sender: Optional[EvmAddress]
    from_address: EvmAddress
    from_nft: EvmAddress
    from_id: int
    to_address: EvmAddress
    to_nft: EvmAddress
    to_id: int
    ccy_address: EvmAddress
    price: int