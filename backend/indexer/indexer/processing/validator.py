from typing import Tuple, Optional
import msgspec

from ..model.evm import EvmFilteredBlock


class BlockValidator:
    def __init__(self):
        self.decoder = msgspec.json.Decoder(type=EvmFilteredBlock)

    def validate_block_data(self, data: bytes) -> Tuple[bool, Optional[str], Optional[EvmFilteredBlock]]:
        """
        Validate block data against EvmFilteredBlock schema using msgspec.
        
        Returns:
            Tuple of (is_valid, error_message, decoded_block)
        """
        try:
            raw_block = self.decoder.decode(data)
            return True, None, raw_block
        except Exception as e:
            return False, str(e), None
