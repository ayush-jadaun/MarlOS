"""Tests for P2P file transfer — uses real files."""

import pytest
import os
import tempfile
import hashlib
from pathlib import Path

from agent.p2p.file_transfer import FileTransferManager, CHUNK_SIZE


@pytest.fixture
def sender(tmp_path):
    return FileTransferManager("sender-node", str(tmp_path / "sender"))


@pytest.fixture
def receiver(tmp_path):
    return FileTransferManager("receiver-node", str(tmp_path / "receiver"))


def make_test_file(tmp_path, content: bytes, name="test.bin") -> str:
    """Create a real test file with given content."""
    path = tmp_path / name
    path.write_bytes(content)
    return str(path)


class TestSmallFileTransfer:
    """Transfer a small text file."""

    def test_transfer_small_file(self, tmp_path, sender, receiver):
        content = b"Hello from MarlOS! This is a test file transfer."
        filepath = make_test_file(tmp_path, content, "hello.txt")

        # Sender prepares file
        metadata, chunks = sender.prepare_file(filepath, job_id="test-job-1")
        assert metadata.filename == "hello.txt"
        assert metadata.total_size == len(content)
        assert metadata.total_chunks == 1  # Small file = 1 chunk
        assert metadata.sha256 == hashlib.sha256(content).hexdigest()

        # Receiver gets metadata
        file_id = receiver.receive_metadata({
            "file_id": metadata.file_id,
            "filename": metadata.filename,
            "total_size": metadata.total_size,
            "total_chunks": metadata.total_chunks,
            "sha256": metadata.sha256,
            "sender_node": metadata.sender_node,
            "job_id": metadata.job_id,
        })

        # Receiver gets chunk
        output_path = receiver.receive_chunk(chunks[0])
        assert output_path is not None

        # Verify received file
        received = Path(output_path).read_bytes()
        assert received == content
        assert hashlib.sha256(received).hexdigest() == metadata.sha256


class TestLargeFileTransfer:
    """Transfer a file larger than chunk size."""

    def test_transfer_multi_chunk(self, tmp_path, sender, receiver):
        # Create a file larger than CHUNK_SIZE (512KB)
        content = os.urandom(CHUNK_SIZE * 3 + 1234)  # ~1.5MB + extra
        filepath = make_test_file(tmp_path, content, "large.bin")

        # Sender prepares
        metadata, chunks = sender.prepare_file(filepath)
        assert metadata.total_chunks == 4  # 3 full chunks + 1 partial
        assert len(chunks) == 4

        # Receiver gets metadata
        receiver.receive_metadata({
            "file_id": metadata.file_id,
            "filename": metadata.filename,
            "total_size": metadata.total_size,
            "total_chunks": metadata.total_chunks,
            "sha256": metadata.sha256,
            "sender_node": metadata.sender_node,
        })

        # Receive chunks out of order (simulating network)
        import random
        shuffled = list(enumerate(chunks))
        random.shuffle(shuffled)

        output_path = None
        for idx, chunk in shuffled:
            result = receiver.receive_chunk(chunk)
            if result:
                output_path = result

        assert output_path is not None
        received = Path(output_path).read_bytes()
        assert len(received) == len(content)
        assert received == content


class TestBinaryFileTransfer:
    """Transfer binary/image-like data."""

    def test_transfer_binary(self, tmp_path, sender, receiver):
        # Simulate a PNG-like binary file
        content = bytes(range(256)) * 100  # 25.6KB of binary data
        filepath = make_test_file(tmp_path, content, "output.png")

        metadata, chunks = sender.prepare_file(filepath)
        receiver.receive_metadata({
            "file_id": metadata.file_id,
            "filename": metadata.filename,
            "total_size": metadata.total_size,
            "total_chunks": metadata.total_chunks,
            "sha256": metadata.sha256,
            "sender_node": metadata.sender_node,
        })

        output_path = None
        for chunk in chunks:
            result = receiver.receive_chunk(chunk)
            if result:
                output_path = result

        received = Path(output_path).read_bytes()
        assert received == content


class TestTransferIntegrity:
    """Test hash verification catches corruption."""

    def test_corrupted_chunk_rejected(self, tmp_path, sender, receiver):
        content = b"important data that must not be corrupted"
        filepath = make_test_file(tmp_path, content)

        metadata, chunks = sender.prepare_file(filepath)
        receiver.receive_metadata({
            "file_id": metadata.file_id,
            "filename": metadata.filename,
            "total_size": metadata.total_size,
            "total_chunks": metadata.total_chunks,
            "sha256": metadata.sha256,
            "sender_node": metadata.sender_node,
        })

        # Corrupt the chunk data
        corrupted = dict(chunks[0])
        corrupted["chunk_hash"] = "0000000000000000000000000000000000000000000000000000000000000000"
        result = receiver.receive_chunk(corrupted)
        assert result is None  # Should reject

    def test_file_not_found(self, sender):
        with pytest.raises(FileNotFoundError):
            sender.prepare_file("/nonexistent/file.txt")


class TestTransferStatus:
    def test_status_tracking(self, tmp_path, sender, receiver):
        content = os.urandom(CHUNK_SIZE * 2 + 100)
        filepath = make_test_file(tmp_path, content)

        metadata, chunks = sender.prepare_file(filepath)
        file_id = receiver.receive_metadata({
            "file_id": metadata.file_id,
            "filename": metadata.filename,
            "total_size": metadata.total_size,
            "total_chunks": metadata.total_chunks,
            "sha256": metadata.sha256,
            "sender_node": metadata.sender_node,
        })

        # Check in-progress status
        status = receiver.get_transfer_status(file_id)
        assert status["status"] == "in_progress"
        assert status["progress"] == 0.0

        # Receive first chunk
        receiver.receive_chunk(chunks[0])
        status = receiver.get_transfer_status(file_id)
        assert status["received"] == 1

        # Complete transfer
        for chunk in chunks[1:]:
            receiver.receive_chunk(chunk)

        status = receiver.get_transfer_status(file_id)
        assert status["status"] == "completed"

    def test_callback_on_complete(self, tmp_path, sender, receiver):
        content = b"callback test data"
        filepath = make_test_file(tmp_path, content)

        callback_results = []
        receiver.on_transfer_complete(lambda fid, path: callback_results.append((fid, path)))

        metadata, chunks = sender.prepare_file(filepath)
        receiver.receive_metadata({
            "file_id": metadata.file_id,
            "filename": metadata.filename,
            "total_size": metadata.total_size,
            "total_chunks": metadata.total_chunks,
            "sha256": metadata.sha256,
            "sender_node": metadata.sender_node,
        })

        for chunk in chunks:
            receiver.receive_chunk(chunk)

        assert len(callback_results) == 1
        assert callback_results[0][0] == metadata.file_id
