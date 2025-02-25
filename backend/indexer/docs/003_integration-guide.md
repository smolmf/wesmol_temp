# Integration Guide

This guide explains how to integrate your existing decoder logic with the BlockDecoder service structure.

## Integrating Your Decoder Logic

### 1. Add Your Decoder to `BlockDataTransformer`

Replace the placeholder implementation in `BlockDataTransformer.decode_block()` with your actual decoder logic:

```python
class BlockDataTransformer:
    """Decodes validated blocks into a standardized format."""
    
    def decode_block(self, block: EvmFilteredBlock) -> Dict[str, Any]:
        """
        Decode a validated block.
        
        Args:
            block: Validated EvmFilteredBlock instance
            
        Returns:
            Dictionary of decoded data
        """
        # Your existing decoder logic goes here
        # This should transform the EvmFilteredBlock into your standardized format
        
        # Example integration:
        return your_existing_decoder.decode(block)
```

### 2. Extend Database Models If Needed

If your decoder needs to track additional metadata:

1. Add fields to the `BlockValidation` model
2. Update the database operations in `BlockValidator`

### 3. Add Custom Error Handling

If your decoder has specific error cases:

1. Update the error handling in `BlockDecoder.process_block()`
2. Add specific error types to the results information

### 4. Testing Your Integration

1. Run the service locally first:
   ```bash
   python -m backend.services.decoder.server.main
   ```

2. Process a test block:
   ```bash
   curl -X POST http://localhost:8080/process -d '{"block_path": "path/to/test/block.json"}'
   ```

## EventIndexer Integration (Future)

When implementing EventIndexer:

1. Create similar component structure:
   - EventExtractor
   - EventMapper
   - DatabaseIndexer

2. Set up Pub/Sub subscription for decoded blocks

3. Connect to the same database but use different models