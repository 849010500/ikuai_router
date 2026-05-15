"""Download and manage ikuai-cli binary."""

import asyncio
import hashlib
import logging
import os
import platform
import stat
import tarfile
import tempfile
import zipfile
from pathlib import Path

import aiohttp

_LOGGER = logging.getLogger(__name__)

IKUAI_CLI_VERSION = "v1.0.2"
IKUAI_CLI_BASE_URL = f"https://github.com/ikuaios/ikuai-cli/releases/download/{IKUAI_CLI_VERSION}"

CHECKSUMS = {
    "ikuai-cli_linux_amd64.tar.gz": "6d50f078b5fc0af8073538a06dc585ddf519162ad3c6e6771be77332f16d76b2",
    "ikuai-cli_linux_arm64.tar.gz": "48e1bad88200ae5dc46490c77ea700df738772b5ccf15bd68f14681dcb3d6301",
    "ikuai-cli_darwin_amd64.tar.gz": "4af73cec7d62c82a00b4da9c70b30c099fe2a4b6ae5771427dc2bc5633c1fc6f",
    "ikuai-cli_darwin_arm64.tar.gz": "65938d44da7303f7411be1b7ee75d4924679717b2444b6999695153367bd322a",
    "ikuai-cli_windows_amd64.zip": "1e32116c068093aaed04b09c7f3b530d4d8c962351d972de68e6afbf23aa74d5"
}

class IkuaiCliDownloader:
    """Download and manage ikuai-cli binary."""
    
    def __init__(self, storage_dir: Path):
        self._storage_dir = storage_dir
        self._binary_path = storage_dir / ("ikuai-cli.exe" if platform.system() == "Windows" else "ikuai-cli")
        self._downloading = False
    
    @property
    def binary_path(self) -> Path:
        """Get the path to the ikuai-cli binary."""
        return self._binary_path
    
    @property
    def is_installed(self) -> bool:
        """Check if ikuai-cli is installed and executable."""
        return self._binary_path.exists() and os.access(self._binary_path, os.X_OK)
    
    def _get_arch_filename(self) -> str:
        """Get the correct filename based on system architecture."""
        system = platform.system().lower()
        machine = platform.machine().lower()
        
        if system == "windows":
            return "ikuai-cli_windows_amd64.zip"
        elif system == "linux":
            if machine in ["x86_64", "amd64"]:
                return "ikuai-cli_linux_amd64.tar.gz"
            elif machine in ["aarch64", "arm64"]:
                return "ikuai-cli_linux_arm64.tar.gz"
            else:
                raise ValueError(f"Unsupported architecture: {machine}")
        elif system == "darwin":
            if machine in ["x86_64", "amd64"]:
                return "ikuai-cli_darwin_amd64.tar.gz"
            elif machine in ["aarch64", "arm64"]:
                return "ikuai-cli_darwin_arm64.tar.gz"
            else:
                raise ValueError(f"Unsupported architecture: {machine}")
        else:
            raise ValueError(f"Unsupported OS: {system}")
    
    def _verify_checksum(self, filepath: Path, expected: str) -> bool:
        """Verify file checksum."""
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest() == expected
    
    def _extract_binary(self, archive_path: Path, filename: str) -> None:
        """Extract binary from archive."""
        if filename.endswith(".tar.gz"):
            with tarfile.open(archive_path, "r:gz") as tar:
                for member in tar.getmembers():
                    if member.name.endswith("ikuai-cli") or member.name.endswith("ikuai-cli.exe"):
                        member.name = self._binary_path.name
                        tar.extract(member, self._storage_dir)
                        break
        elif filename.endswith(".zip"):
            with zipfile.ZipFile(archive_path, "r") as zip_ref:
                for zip_info in zip_ref.infolist():
                    if zip_info.filename.endswith("ikuai-cli.exe"):
                        zip_info.filename = self._binary_path.name
                        zip_ref.extract(zip_info, self._storage_dir)
                        break
    
    async def download(self) -> bool:
        """Download and install ikuai-cli."""
        if self._downloading:
            _LOGGER.warning("Download already in progress")
            return False
        
        self._downloading = True
        
        try:
            filename = self._get_arch_filename()
            download_url = f"{IKUAI_CLI_BASE_URL}/{filename}"
            checksum = CHECKSUMS.get(filename)
            
            _LOGGER.info("Downloading ikuai-cli from: %s", download_url)
            
            # Create storage directory if it doesn't exist
            self._storage_dir.mkdir(parents=True, exist_ok=True)
            
            # Download the archive
            async with aiohttp.ClientSession() as session:
                async with session.get(download_url, timeout=aiohttp.ClientTimeout(total=300)) as response:
                    if response.status != 200:
                        _LOGGER.error("Failed to download ikuai-cli: HTTP %d", response.status)
                        return False
                    
                    # Save to temporary file
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".tmp") as tmp_file:
                        tmp_path = Path(tmp_file.name)
                        async for chunk in response.content.iter_chunked(8192):
                            tmp_file.write(chunk)
            
            # Verify checksum
            if checksum and not self._verify_checksum(tmp_path, checksum):
                _LOGGER.error("Checksum verification failed for ikuai-cli")
                tmp_path.unlink()
                return False
            
            # Extract binary
            self._extract_binary(tmp_path, filename)
            
            # Set executable permission
            if platform.system() != "Windows":
                self._binary_path.chmod(self._binary_path.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
            
            # Clean up
            tmp_path.unlink()
            
            _LOGGER.info("ikuai-cli installed successfully at: %s", self._binary_path)
            return True
            
        except Exception as e:
            _LOGGER.error("Failed to download ikuai-cli: %s", e)
            return False
        finally:
            self._downloading = False
    
    async def ensure_installed(self) -> bool:
        """Ensure ikuai-cli is installed, downloading if necessary."""
        if self.is_installed:
            return True
        
        return await self.download()