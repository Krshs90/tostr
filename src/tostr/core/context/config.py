import tomllib
from pathlib import Path

from loguru import logger
import os

class ProjectConfig:
    def __init__(self, tostr_path: Path):
        self.toml_config = {}
        toml_path = tostr_path / "config.toml"
        if toml_path.exists():
            with open(toml_path, 'rb') as f:
                self.toml_config = tomllib.load(f)
            logger.debug(f"Loaded configuration from {toml_path}")
        else:
            logger.debug("No config.toml file found, proceeding with default configuration.")

        self.path_ignore = set()
        ignore_path = tostr_path / ".tostrignore"
        if ignore_path.exists():
            with open(ignore_path, 'r') as f:
                self.path_ignore = {line.strip() for line in f}
            logger.info(f"Loaded path ignore rules from {ignore_path}: {self.path_ignore}")
        else:
            # self.path_ignore = {"venv", ".venv", "env", ".env", "build", "dist", "__pycache__", ".tostr", ".git"}
            open(ignore_path, 'w').close()  # Create empty .tostrignore file
            logger.debug("No .tostrignore file found, proceeding without path ignore rules.")
    
    