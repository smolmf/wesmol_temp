# backend/scripts/fix_block.py
#!/usr/bin/env python3
"""
Script for manually fixing or patching specific blocks.
For cases where standard reprocessing doesn't resolve the issue.
"""

import sys
import argparse
import json
from pathlib import Path

# Add the project root to the path
script_dir = Path(__file__).resolve().parent
backend_dir = script_dir.parent
sys.path.append(str(backend_dir))

# Import our packages
from indexer.indexer.env import env
from indexer.indexer.database.operations.session import DatabaseManager
from indexer.indexer.database.operations.validator import BlockValidator
from indexer.indexer.database.models.status import ProcessingStatus
from backend.indexer.indexer.storage.base import GCSHandler

def load_block(block_number: int, raw: bool = True) -> dict:
    """Load a block from storage."""
    gcs_handler = GCSHandler(env.get_bucket_name())
    
    # Determine path based on whether we want raw or decoded
    prefix = "raw/" if raw else "decoded/"
    path = f"{prefix}block_{block_number}.json"
    
    # Load the data
    data = gcs_handler.download_blob_as_text(path)
    if not data:
        raise ValueError(f"Block {block_number} not found at {path}")
    
    return json.loads(data)

def save_block(block_number: int, data: dict, raw: bool = False) -> bool:
    """Save a block to storage."""
    gcs_handler = GCSHandler(env.get_bucket_name())
    
    # Determine path based on whether this is raw or decoded
    prefix = "raw/" if raw else "decoded/"
    path = f"{prefix}block_{block_number}.json"
    
    # Save the data
    return gcs_handler.upload_blob_from_string(
        json.dumps(data, indent=2),
        path,
        content_type="application/json"
    )

def reset_block_status(block_number: int) -> bool:
    """Reset a block's processing status to pending."""
    db_manager = DatabaseManager(env.get_db_url())
    validator = BlockValidator(db_manager)
    
    # Reset the status
    validator.update_status(
        block_number=block_number,
        status=ProcessingStatus.PENDING
    )
    return True

def examine_block(block_number: int, raw: bool = True) -> None:
    """Examine a block and print its contents."""
    try:
        data = load_block(block_number, raw)
        print(json.dumps(data, indent=2))
    except Exception as e:
        print(f"Error loading block {block_number}: {e}")

def patch_block(block_number: int, patch_file: str, raw: bool = False) -> None:
    """Apply a JSON patch to a block."""
    try:
        # Load the block
        data = load_block(block_number, raw)
        
        # Load the patch
        with open(patch_file, 'r') as f:
            patch = json.load(f)
        
        # Apply the patch (simple dictionary update)
        data.update(patch)
        
        # Save the block
        save_block(block_number, data, raw)
        print(f"Successfully patched block {block_number}")
        
        # Reset status so it can be reprocessed
        if raw:
            reset_block_status(block_number)
            print(f"Reset status for block {block_number}")
            
    except Exception as e:
        print(f"Error patching block {block_number}: {e}")

def main():
    """Main entry point for fix script."""
    parser = argparse.ArgumentParser(description="Manually fix blocks")
    
    # Command selection
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Examine command
    examine_parser = subparsers.add_parser('examine', help='Examine a block')
    examine_parser.add_argument('block_number', type=int, help='Block number to examine')
    examine_parser.add_argument('--decoded', action='store_true', help='Examine decoded block instead of raw')
    
    # Patch command
    patch_parser = subparsers.add_parser('patch', help='Apply a patch to a block')
    patch_parser.add_argument('block_number', type=int, help='Block number to patch')
    patch_parser.add_argument('patch_file', type=str, help='JSON file containing patch')
    patch_parser.add_argument('--decoded', action='store_true', help='Patch decoded block instead of raw')
    
    # Reset command
    reset_parser = subparsers.add_parser('reset', help='Reset block status')
    reset_parser.add_argument('block_number', type=int, help='Block number to reset')
    
    args = parser.parse_args()
    
    if args.command == 'examine':
        examine_block(args.block_number, not args.decoded)
    elif args.command == 'patch':
        patch_block(args.block_number, args.patch_file, not args.decoded)
    elif args.command == 'reset':
        reset_block_status(args.block_number)
        print(f"Reset status for block {args.block_number}")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()