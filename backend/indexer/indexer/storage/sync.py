import os
import json
import time
import hashlib
from typing import Dict, List, Any, Optional, Tuple, Union, Callable
from datetime import datetime, timezone
from tqdm import tqdm

from backend.indexer.indexer.storage.base import GCSHandler

class GCSLocalSync:
    """
    Synchronizes a Google Cloud Storage bucket to local storage with file renaming.
    Uses GCSHandler for all GCS operations, with efficient change detection.
    """
    
    def __init__(self, gcs_handler: GCSHandler, local_dir: str, 
                 metadata_file: str = '.gcs_sync_metadata.json'):
        """
        Initialize the sync tool.
        
        Args:
            gcs_handler: Instance of GCSHandler for GCS operations
            local_dir: Local directory to sync files to
            metadata_file: File to store sync metadata
        """
        self.gcs_handler = gcs_handler
        self.local_dir = local_dir
        self.metadata_file = os.path.join(local_dir, metadata_file)
        
        # Create local directory if it doesn't exist
        os.makedirs(local_dir, exist_ok=True)
        
        # Load or initialize metadata
        self.metadata = self._load_metadata()
    
    def _load_metadata(self) -> Dict[str, Any]:
        """Load metadata from file or create new if doesn't exist."""
        if os.path.exists(self.metadata_file):
            with open(self.metadata_file, 'r') as f:
                return json.load(f)
        else:
            return {
                'last_sync': None,
                'last_sync_timestamp': None,
                'file_versions': {},
                'files': {}
            }
    
    def _save_metadata(self) -> None:
        """Save current metadata to file."""
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)
    
    def rename_file(self, gcs_path: str) -> str:
        """
        Convert GCS file path to local file path with renaming rules.
        Override this method to implement your specific renaming logic.
        
        Args:
            gcs_path: Original GCS file path
            
        Returns:
            Local file path after renaming
        """
        # Default implementation: simply use the base name
        # Replace this with your own renaming logic
        base_name = os.path.basename(gcs_path)
        
        # Example renaming: replace spaces with underscores and lowercase
        local_name = base_name.replace(' ', '_').lower()
        
        return os.path.join(self.local_dir, local_name)
    
    def compute_local_hash(self, file_path: str) -> Optional[str]:
        """
        Compute an MD5 hash for a local file.
        
        Args:
            file_path: Path to the local file
            
        Returns:
            MD5 hash as hex string, or None if file doesn't exist
        """
        if not os.path.exists(file_path):
            return None
            
        hasher = hashlib.md5()
        with open(file_path, 'rb') as f:
            buf = f.read(65536)
            while len(buf) > 0:
                hasher.update(buf)
                buf = f.read(65536)
        return hasher.hexdigest()
    
    def sync(self, prefix: Optional[str] = None, dry_run: bool = False, 
             force: bool = False, progress_callback: Optional[Callable] = None) -> Dict[str, int]:
        """
        Synchronize GCS bucket to local storage using efficient change detection.
        
        Args:
            prefix: Only sync files with this prefix
            dry_run: If True, don't actually download files
            force: If True, download all files regardless of hash
            progress_callback: Optional callback function for progress updates
            
        Returns:
            Dictionary with sync statistics
        """
        stats = {
            'new_files': 0,
            'updated_files': 0,
            'unchanged_files': 0,
            'deleted_files': 0,
            'total_bytes': 0,
            'errors': 0
        }
        
        print(f"Checking for changes in GCS bucket '{self.gcs_handler.bucket_name}'...")
        
        # If we have a previous sync, use efficient change detection
        if not force and self.metadata['file_versions'] and self.metadata['last_sync_timestamp']:
            # Get changed, new, and deleted files since last sync
            changed_files, new_files, deleted_files = self.gcs_handler.get_changed_files(
                self.metadata['file_versions'], prefix)
            
            print(f"Found {len(new_files)} new files, {len(changed_files)} changed files, and {len(deleted_files)} deleted files")
            
            # Process new and changed files
            files_to_process = [(name, "new") for name in new_files] + [(name, "changed") for name in changed_files]
            
            # Update stats for deleted files
            for gcs_path in deleted_files:
                if gcs_path in self.metadata['files']:
                    print(f"Deleted: {gcs_path}")
                    del self.metadata['files'][gcs_path]
                    stats['deleted_files'] += 1
            
        else:
            # For first sync or forced sync, get all files
            print("Performing full bucket scan...")
            blobs = self.gcs_handler.list_blobs(prefix)
            files_to_process = [(blob.name, "new" if blob.name not in self.metadata['files'] else "check") 
                              for blob in blobs]
            print(f"Found {len(files_to_process)} files in bucket")
        
        # Get current blob versions for metadata update
        current_versions = self.gcs_handler.list_blobs_with_versions(prefix)
        
        # Process files
        for gcs_path, status in tqdm(files_to_process, desc="Processing files"):
            try:
                # Get the blob
                blob = self.gcs_handler.get_blob(gcs_path)
                if not blob:
                    tqdm.write(f"Warning: Could not get blob for {gcs_path}")
                    continue
                
                # Get the local path after renaming
                local_path = self.rename_file(gcs_path)
                rel_local_path = os.path.relpath(local_path, self.local_dir)
                
                # Determine if we need to download
                need_download = False
                
                if force:
                    need_download = True
                    status = "forced"
                elif status == "new":
                    need_download = True
                elif status == "changed":
                    need_download = True
                elif status == "check":
                    # Check if the blob version has changed
                    if gcs_path in self.metadata['file_versions']:
                        old_version = self.metadata['file_versions'][gcs_path]
                        new_version = current_versions[gcs_path]
                        
                        if (old_version['generation'] != new_version['generation'] or
                            old_version['metageneration'] != new_version['metageneration'] or
                            old_version['md5_hash'] != new_version['md5_hash']):
                            need_download = True
                            status = "changed"
                        else:
                            # Also check if the local file exists and has the right hash
                            if gcs_path in self.metadata['files']:
                                expected_hash = self.metadata['files'][gcs_path]['local_hash']
                                local_hash = self.compute_local_hash(local_path)
                                
                                if local_hash != expected_hash:
                                    need_download = True
                                    status = "local changed"
                                else:
                                    status = "unchanged"
                    else:
                        # No previous version info, need to download
                        need_download = True
                        status = "new"
                
                # Download the file if needed
                if need_download and not dry_run:
                    os.makedirs(os.path.dirname(local_path), exist_ok=True)
                    self.gcs_handler.download_blob_to_file(gcs_path, local_path)
                    local_hash = self.compute_local_hash(local_path)
                    
                    # Update metadata
                    self.metadata['files'][gcs_path] = {
                        'local_path': rel_local_path,
                        'local_hash': local_hash,
                        'size': blob.size,
                        'last_updated': time.time()
                    }
                    
                    # Update file versions
                    self.metadata['file_versions'][gcs_path] = current_versions[gcs_path]
                    
                    # Update stats
                    if status == "new":
                        stats['new_files'] += 1
                    else:
                        stats['updated_files'] += 1
                    stats['total_bytes'] += blob.size
                else:
                    # For unchanged files, still update the file versions
                    if gcs_path in current_versions:
                        self.metadata['file_versions'][gcs_path] = current_versions[gcs_path]
                    
                    stats['unchanged_files'] += 1
                
                tqdm.write(f"{status}: {gcs_path} -> {rel_local_path}")
                
                # Call progress callback if provided
                if progress_callback:
                    progress_callback(gcs_path, local_path, status)
                
            except Exception as e:
                tqdm.write(f"Error processing {gcs_path}: {str(e)}")
                stats['errors'] += 1
        
        # Update last sync time
        current_time = datetime.now(timezone.utc)
        self.metadata['last_sync'] = time.time()
        self.metadata['last_sync_timestamp'] = current_time.isoformat()
        
        # Save metadata
        if not dry_run:
            self._save_metadata()
        
        return stats

    def reverse_lookup(self, local_file: str) -> Optional[str]:
        """
        Find the GCS file path for a local file.
        
        Args:
            local_file: Local file path
            
        Returns:
            GCS file path if found, None otherwise
        """
        rel_path = os.path.relpath(local_file, self.local_dir) if os.path.isabs(local_file) else local_file
        
        for gcs_path, info in self.metadata['files'].items():
            if info['local_path'] == rel_path:
                return gcs_path
                
        return None
    
    def verify_integrity(self) -> List[Dict[str, str]]:
        """
        Verify that all local files match their expected hashes.
        
        Returns:
            List of files with integrity issues
        """
        issues = []
        
        for gcs_path, info in tqdm(self.metadata['files'].items(), desc="Verifying local files"):
            local_path = os.path.join(self.local_dir, info['local_path'])
            
            if not os.path.exists(local_path):
                issues.append({
                    'gcs_path': gcs_path,
                    'local_path': local_path,
                    'issue': 'missing'
                })
                continue
                
            local_hash = self.compute_local_hash(local_path)
            if local_hash != info['local_hash']:
                issues.append({
                    'gcs_path': gcs_path,
                    'local_path': local_path,
                    'issue': 'hash mismatch',
                    'expected': info['local_hash'],
                    'actual': local_hash
                })
                
        return issues
    
    def get_local_path(self, gcs_path: str, force_download: bool = False) -> Optional[str]:
        """
        Get the local path for a GCS file, downloading it if necessary.
        
        Args:
            gcs_path: GCS file path
            force_download: Force download even if file exists
            
        Returns:
            Local file path if successful, None otherwise
        """
        # Get the local path after renaming
        local_path = self.rename_file(gcs_path)
        
        # Check if we need to download
        if force_download or not os.path.exists(local_path):
            # Get the blob
            blob = self.gcs_handler.get_blob(gcs_path)
            if not blob:
                return None
                
            # Download the file
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            self.gcs_handler.download_blob_to_file(gcs_path, local_path)
            
            # Update metadata
            local_hash = self.compute_local_hash(local_path)
            rel_local_path = os.path.relpath(local_path, self.local_dir)
            
            # Get version info for the blob
            version_info = {
                'generation': blob.generation,
                'metageneration': blob.metageneration,
                'updated': blob.updated.isoformat() if blob.updated else None,
                'md5_hash': blob.md5_hash,
                'size': blob.size
            }
            
            self.metadata['files'][gcs_path] = {
                'local_path': rel_local_path,
                'local_hash': local_hash,
                'size': blob.size,
                'last_updated': time.time()
            }
            
            self.metadata['file_versions'][gcs_path] = version_info
            
            self._save_metadata()
        
        return local_path