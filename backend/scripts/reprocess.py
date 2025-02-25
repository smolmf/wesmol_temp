# backend/scripts/reprocess.py
#!/usr/bin/env python3
"""
Script for reprocessing blocks with errors or that need decoder updates.
Runs as a standalone script outside of Cloud Run.
"""

import os
import sys
import argparse
import json
import requests
from pathlib import Path
from typing import List, Optional
from tqdm import tqdm

# Add the project root to the path so we can import our packages
script_dir = Path(__file__).resolve().parent
backend_dir = script_dir.parent
sys.path.append(str(backend_dir))

# Import our packages
from indexer.indexer.env import env
from indexer.indexer.database.operations.session import DatabaseManager
from indexer.indexer.database.operations.validator import BlockValidator
from indexer.indexer.database.models.status import ProcessingStatus
from backend.indexer.indexer.storage.base import GCSHandler

def get_invalid_blocks(limit: int = None) -> List[int]:
    """Get list of blocks with validation/processing issues."""
    db_manager = DatabaseManager(env.get_db_url())
    validator = BlockValidator(db_manager)
    
    invalid_blocks = validator.get_blocks_by_status(ProcessingStatus.INVALID, limit=limit)
    return [block.block_number for block in invalid_blocks]

def reprocess_blocks_via_api(block_numbers: List[int], api_url: str) -> dict:
    """
    Reprocess blocks by calling the processor API.
    
    Args:
        block_numbers: List of block numbers to reprocess
        api_url: URL of the processor service
        
    Returns:
        API response as dictionary
    """
    endpoint = f"{api_url.rstrip('/')}/reprocess"
    
    # Call the API
    response = requests.post(
        endpoint,
        json={"block_numbers": block_numbers},
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code != 200:
        raise Exception(f"API call failed with status {response.status_code}: {response.text}")
    
    return response.json()

def reprocess_blocks_direct(block_numbers: List[int]) -> dict:
    """
    Reprocess blocks directly (without calling API).
    
    This is useful if the processor service isn't running or you want to
    bypass it for some reason. It does the processing in-process.
    
    Args:
        block_numbers: List of block numbers to reprocess
        
    Returns:
        Processing results
    """
    # Initialize services
    db_manager = DatabaseManager(env.get_db_url())
    validator = BlockValidator(db_manager)
    gcs_handler = GCSHandler(env.get_bucket_name())
    
    # Import processor here to avoid circular imports
    from backend.indexer.indexer.processing.processor import BlockProcessor, BlockValidator as ProcessValidator, BlockDecoder, BlockStorage
    
    # Initialize processor
    processor = BlockProcessor(
        gcs_handler=gcs_handler,
        status_tracker=validator,
        validator=ProcessValidator(),
        decoder=BlockDecoder(),
        storage=BlockStorage(gcs_handler)
    )
    
    # Process blocks
    return processor.reprocess_blocks(block_numbers)

def main():
    """Main entry point for reprocessing script."""
    parser = argparse.ArgumentParser(description="Reprocess blocks with errors")
    
    # Mode selection
    parser.add_argument("--mode", choices=["api", "direct"], default="api",
                       help="How to reprocess: via API or directly")
    
    # Block selection
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--all-invalid", action="store_true", 
                      help="Reprocess all invalid blocks")
    group.add_argument("--blocks", type=int, nargs="+",
                      help="Specific block numbers to reprocess")
    group.add_argument("--file", type=str,
                      help="File containing block numbers (one per line)")
    
    # Limits and API settings
    parser.add_argument("--limit", type=int, default=100,
                       help="Max number of blocks to process (for --all-invalid)")
    parser.add_argument("--api-url", type=str,
                       help="URL of processor API (for --mode=api)")
    
    args = parser.parse_args()
    
    # Get blocks to process
    if args.all_invalid:
        block_numbers = get_invalid_blocks(args.limit)
        print(f"Found {len(block_numbers)} invalid blocks to reprocess")
    elif args.blocks:
        block_numbers = args.blocks
        print(f"Will reprocess {len(block_numbers)} specified blocks")
    elif args.file:
        with open(args.file, 'r') as f:
            block_numbers = [int(line.strip()) for line in f if line.strip().isdigit()]
        print(f"Read {len(block_numbers)} block numbers from {args.file}")
    
    if not block_numbers:
        print("No blocks to process")
        return
    
    # Reprocess blocks
    if args.mode == "api":
        if not args.api_url:
            # Try to get from environment
            api_url = os.getenv("PROCESSOR_API_URL")
            if not api_url:
                print("Error: --api-url is required for API mode")
                return
        else:
            api_url = args.api_url
            
        print(f"Reprocessing {len(block_numbers)} blocks via API at {api_url}")
        results = reprocess_blocks_via_api(block_numbers, api_url)
    else:
        print(f"Reprocessing {len(block_numbers)} blocks directly")
        results = reprocess_blocks_direct(block_numbers)
    
    # Print results
    print(f"\nReprocessing complete:")
    print(f"  Total: {results['total']}")
    print(f"  Success: {results['success']}")
    print(f"  Failure: {results['failure']}")
    
    # Output detailed results to a file
    output_file = f"reprocess_results_{int(time.time())}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nDetailed results saved to {output_file}")

if __name__ == "__main__":
    main()