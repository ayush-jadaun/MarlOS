"""
P2P File Transfer for MarlOS
Transfers job outputs between nodes using chunked, signed messages.
Used by the pipeline engine to pass artifacts from one step to the next.
"""

import asyncio
import base64
import hashlib
import os
import time
import uuid
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Max chunk size: 512KB (fits within ZMQ message limits)
CHUNK_SIZE = 512 * 1024


@dataclass
class FileMetadata:
    """Metadata for a file being transferred."""
    file_id: str
    filename: str
    total_size: int
    total_chunks: int
    sha256: str
    sender_node: str
    job_id: str = ""
    created_at: float = field(default_factory=time.time)


@dataclass
class TransferState:
    """Tracks state of an ongoing file transfer."""
    metadata: FileMetadata
    received_chunks: dict[int, bytes] = field(default_factory=dict)
    completed: bool = False
    output_path: str = None

    @property
    def progress(self) -> float:
        if self.metadata.total_chunks == 0:
            return 1.0
        return len(self.received_chunks) / self.metadata.total_chunks


class FileTransferManager:
    """Manages file sending and receiving over the P2P network."""

    def __init__(self, node_id: str, data_dir: str = "./data"):
        self.node_id = node_id
        self.data_dir = Path(data_dir)
        self.transfers_dir = self.data_dir / "transfers"
        self.transfers_dir.mkdir(parents=True, exist_ok=True)

        # Active transfers (receiving)
        self.incoming: dict[str, TransferState] = {}
        # Completed transfers
        self.completed: dict[str, str] = {}  # file_id -> output_path
        # Callbacks
        self._on_complete_callbacks = []

    def on_transfer_complete(self, callback):
        """Register callback for when a transfer completes."""
        self._on_complete_callbacks.append(callback)

    def prepare_file(self, filepath: str, job_id: str = "") -> tuple[FileMetadata, list[dict]]:
        """
        Prepare a file for transfer by chunking and hashing.
        Returns (metadata, list_of_chunk_messages).
        """
        filepath = Path(filepath)
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        file_data = filepath.read_bytes()
        file_id = f"file-{str(uuid.uuid4())[:8]}"

        # Calculate hash
        sha256 = hashlib.sha256(file_data).hexdigest()

        # Split into chunks
        chunks = []
        for i in range(0, len(file_data), CHUNK_SIZE):
            chunk = file_data[i:i + CHUNK_SIZE]
            chunks.append(chunk)

        metadata = FileMetadata(
            file_id=file_id,
            filename=filepath.name,
            total_size=len(file_data),
            total_chunks=len(chunks),
            sha256=sha256,
            sender_node=self.node_id,
            job_id=job_id,
        )

        chunk_messages = []
        for idx, chunk in enumerate(chunks):
            chunk_messages.append({
                "file_id": file_id,
                "chunk_index": idx,
                "data": base64.b64encode(chunk).decode("ascii"),
                "chunk_hash": hashlib.sha256(chunk).hexdigest(),
            })

        return metadata, chunk_messages

    def receive_metadata(self, metadata_dict: dict) -> str:
        """Process incoming file metadata. Returns file_id."""
        metadata = FileMetadata(
            file_id=metadata_dict["file_id"],
            filename=metadata_dict["filename"],
            total_size=metadata_dict["total_size"],
            total_chunks=metadata_dict["total_chunks"],
            sha256=metadata_dict["sha256"],
            sender_node=metadata_dict["sender_node"],
            job_id=metadata_dict.get("job_id", ""),
        )

        self.incoming[metadata.file_id] = TransferState(metadata=metadata)
        logger.info(f"[FILE] Receiving {metadata.filename} ({metadata.total_size} bytes, {metadata.total_chunks} chunks)")
        return metadata.file_id

    def receive_chunk(self, chunk_msg: dict) -> Optional[str]:
        """
        Process an incoming chunk. Returns output_path if transfer is complete, else None.
        """
        file_id = chunk_msg["file_id"]
        transfer = self.incoming.get(file_id)
        if not transfer:
            logger.warning(f"[FILE] Received chunk for unknown transfer: {file_id}")
            return None

        chunk_index = chunk_msg["chunk_index"]
        chunk_data = base64.b64decode(chunk_msg["data"])

        # Verify chunk integrity
        expected_hash = chunk_msg.get("chunk_hash")
        if expected_hash:
            actual_hash = hashlib.sha256(chunk_data).hexdigest()
            if actual_hash != expected_hash:
                logger.error(f"[FILE] Chunk {chunk_index} hash mismatch for {file_id}")
                return None

        transfer.received_chunks[chunk_index] = chunk_data

        # Check if complete
        if len(transfer.received_chunks) == transfer.metadata.total_chunks:
            return self._assemble_file(transfer)

        return None

    def _assemble_file(self, transfer: TransferState) -> str:
        """Assemble chunks into complete file."""
        # Reassemble in order
        data = b""
        for i in range(transfer.metadata.total_chunks):
            data += transfer.received_chunks[i]

        # Verify full file hash
        actual_hash = hashlib.sha256(data).hexdigest()
        if actual_hash != transfer.metadata.sha256:
            logger.error(f"[FILE] File hash mismatch: expected {transfer.metadata.sha256}, got {actual_hash}")
            return None

        # Write to disk
        output_path = self.transfers_dir / f"{transfer.metadata.file_id}_{transfer.metadata.filename}"
        output_path.write_bytes(data)

        transfer.completed = True
        transfer.output_path = str(output_path)
        self.completed[transfer.metadata.file_id] = str(output_path)

        logger.info(f"[FILE] Transfer complete: {transfer.metadata.filename} -> {output_path}")

        # Notify callbacks
        for cb in self._on_complete_callbacks:
            try:
                cb(transfer.metadata.file_id, str(output_path))
            except Exception as e:
                logger.error(f"[FILE] Callback error: {e}")

        return str(output_path)

    def get_transfer_status(self, file_id: str) -> Optional[dict]:
        """Get status of a transfer."""
        if file_id in self.completed:
            return {"file_id": file_id, "status": "completed", "path": self.completed[file_id]}

        transfer = self.incoming.get(file_id)
        if transfer:
            return {
                "file_id": file_id,
                "status": "in_progress",
                "progress": transfer.progress,
                "received": len(transfer.received_chunks),
                "total": transfer.metadata.total_chunks,
            }

        return None

    def get_file_path(self, file_id: str) -> Optional[str]:
        """Get the local path of a completed transfer."""
        return self.completed.get(file_id)

    def get_missing_chunks(self, file_id: str) -> list[int]:
        """Get list of chunk indices not yet received. Used for retry requests."""
        transfer = self.incoming.get(file_id)
        if not transfer:
            return []
        all_indices = set(range(transfer.metadata.total_chunks))
        received = set(transfer.received_chunks.keys())
        return sorted(all_indices - received)

    def is_transfer_stale(self, file_id: str, timeout: float = 60.0) -> bool:
        """Check if a transfer has stalled (no new chunks within timeout)."""
        transfer = self.incoming.get(file_id)
        if not transfer or transfer.completed:
            return False
        return (time.time() - transfer.metadata.created_at) > timeout
