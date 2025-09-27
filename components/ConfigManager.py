import os
import configparser
import threading
from pathlib import Path
from typing import Optional

_write_lock = threading.Lock()


def _get_base_dir():
    return os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))


class ConfigManager:
    """Encapsulates reading/writing the application's INI configuration.

    - Keeps backward-compatible function wrappers `read_config`/`write_config`.
    - Thread-safe writes via an internal lock.
    """

    def __init__(self, config_path: Optional[str] = None):
        base_dir = _get_base_dir()
        if config_path is None:
            config_path = os.path.join(base_dir, "config.ini")
        else:
            config_path = os.path.abspath(config_path)

        self.base_dir = base_dir
        self.config_path = config_path
        self.default_config_path = os.path.join(base_dir, "config", "config_default")

        self.config = configparser.ConfigParser()
        self.config.optionxform = str

        # load immediately
        self.read()

    def create_default_config(self) -> None:
        if not os.path.exists(self.config_path):
            if os.path.exists(self.default_config_path):
                try:
                    os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
                    with open(self.default_config_path, 'r', encoding='utf-8') as src, open(self.config_path, 'w', encoding='utf-8') as dst:
                        dst.write(src.read())
                except IOError:
                    raise
            else:
                raise FileNotFoundError(f"Default config file not found at {self.default_config_path}")

    def read(self) -> configparser.ConfigParser:
        """Read the INI file, merge defaults and persist merged result."""
        if not os.path.exists(self.config_path):
            self.create_default_config()
            self.config.read(self.config_path, encoding="utf-8")
        else:
            try:
                self.config.read(self.config_path, encoding="utf-8")
            except UnicodeDecodeError:
                try:
                    self.config.read(self.config_path, encoding="gbk")
                except Exception:
                    self.create_default_config()
                    self.config.read(self.config_path, encoding="utf-8")
            except configparser.MissingSectionHeaderError:
                self.create_default_config()
                self.config.read(self.config_path, encoding="utf-8")
            except Exception:
                self.create_default_config()
                self.config.read(self.config_path, encoding="utf-8")

        # merge defaults
        default_cfg = configparser.ConfigParser()
        default_cfg.optionxform = str
        if os.path.exists(self.default_config_path):
            try:
                default_cfg.read(self.default_config_path, encoding="utf-8")
            except Exception:
                pass

        for section_name in default_cfg.sections():
            if not self.config.has_section(section_name):
                self.config.add_section(section_name)
            for option_name, option_value in default_cfg.items(section_name):
                if not self.config.has_option(section_name, option_name):
                    self.config.set(section_name, option_name, option_value)

        # persist merged (best-effort)
        try:
            self.write(self.config)
        except Exception:
            pass

        return self.config

    def write(self, config: Optional[configparser.ConfigParser] = None) -> None:
        if config is None:
            config = self.config

        clean_config = configparser.ConfigParser()
        clean_config.optionxform = str
        for section_name in config.sections():
            if not clean_config.has_section(section_name):
                clean_config.add_section(section_name)
            section_items = {}
            for key, value in config.items(section_name):
                lower_key = key.lower()
                section_items[lower_key] = (key, value)

            for _, (original_key, value) in section_items.items():
                clean_config.set(section_name, original_key, value)

        os.makedirs(os.path.dirname(self.config_path) or self.base_dir, exist_ok=True)
        with _write_lock:
            with open(self.config_path, 'w', encoding='utf-8') as configfile:
                clean_config.write(configfile)


def read_config(config_path: str = None) -> configparser.ConfigParser:
    """Compatibility wrapper: read_config(config_path) -> ConfigParser"""
    mgr = ConfigManager(config_path)
    return mgr.config


def write_config(config: configparser.ConfigParser, config_path: str = None) -> None:
    """Compatibility wrapper: write_config(config, config_path)"""
    mgr = ConfigManager(config_path)
    mgr.write(config)
