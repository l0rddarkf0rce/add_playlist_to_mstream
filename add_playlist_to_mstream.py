#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   Program name: aadd_playlist_to_mstream.py
   Date Created: 2026/02/16
   Version:      1.5
   Author:       Jose Cintron
   E-mail:       l0rddarkf0rce@yahoo.com

Description
-----------
Add one or many .m3u playlists to an mStream server via its public REST API.

Usage
-----
# add a single playlist
python -m mstream_add_playlist -p /path/to/playlist.m3u

# add every .m3u file in a directory (non-recursive)
python -m mstream_add_playlist -p /path/to/playlists/

Features
--------
* Reads configuration from environment variables **or** a ``.env`` file placed next
  to the script.
* Validates required configuration before doing any work.
* Handles HTTP errors with clear log messages.
* Accepts either a single ``.m3u`` file or a directory containing many (non-recursive).
* All public functions are type-annotated and unit-testable.
* Logging level can be overridden with the ``PYTHON_LOGGING`` environment variable.

Revision History:
   2026/02/16     Original code created
   2026/02/17     Documentation added and code clean up
"""

# --------------------------------------------------------------------------- #
# Imports
# --------------------------------------------------------------------------- #
from __future__ import annotations
import logging
import os
import sys
from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import Final, List
import requests
from dotenv import load_dotenv

# --------------------------------------------------------------------------- #
# Configuration & Logging
# --------------------------------------------------------------------------- #
# Load a `.env` file if it exists in the same folder as the script.
load_dotenv(dotenv_path=Path(__file__).with_name(".env"))

# ----- Environment ---------------------------------------------------------- #
class Settings:
    """Container for all configuration values required by the script."""
    BASE_URL: Final[str] = os.getenv("MS_BASE_URL", "http://127.0.0.1:3000").rstrip("/")
    USERNAME: Final[str] = os.getenv("MS_USERNAME", "admin")
    PASSWORD: Final[str] = os.getenv("MS_PASSWORD", "admin")
	
	# ------------------------------------------------------------------ #
    # Explicit list of keys we care about – easy to extend/maintain
    # ------------------------------------------------------------------ #
    _REQUIRED_KEYS = ("BASE_URL", "USERNAME", "PASSWORD")

    @classmethod
    def validate(cls) -> None:
        """Raise an error if any required value is missing or empty."""
        missing = [
            name
            for name in cls._REQUIRED_KEYS
            if not getattr(cls, name, None)
        ]
        if missing:
            raise RuntimeError(f"Missing configuration for: {', '.join(missing)}")
            
# ----- Logging -------------------------------------------------------------- #
def _setup_logging() -> logging.Logger:
    """
    Configure the root logger.  Verbosity can be overridden with
    the `PYTHON_LOGGING` environment variable (e.g. `DEBUG`).
    """
    level = os.getenv("PYTHON_LOGGING", "INFO").upper()
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
        datefmt="%H:%M:%S",
    )
    return logging.getLogger(__name__)

log = _setup_logging()

# --------------------------------------------------------------------------- #
# Helper / Core functions
# --------------------------------------------------------------------------- #
def parse_m3u(file_path: Path) -> List[str]:
    """
    Read a ``.m3u`` file and return a list of non-comment entries.

    Parameters
    ----------
    Path
        Path to the playlist

    Returns
    -------
    List of songs found in the playlist
    """
    if not file_path.is_file():
        raise FileNotFoundError(f"The file {file_path!s} does not exist")

    songs: List[str] = []
    with file_path.open("r", encoding="utf-8", errors="ignore") as f:
        for raw_line in f:
            line = raw_line.strip()
            if line and not line.startswith("#"):
                songs.append(line)

    return songs

def gather_m3u_files(root: Path) -> List[Path]:
    """
    Return a **non-recursive** list of ``.m3u`` files.

    Parameters
    ----------
    Path
        Path to the file or folder to be processed

    Returns
    -------
    * If *root* is a file, the function returns a one-element list (after
      verifying the suffix).
    * If *root* is a directory, only files directly inside that directory are
      handled.
    """
    if root.is_file():
        if root.suffix.lower() != ".m3u":
            raise ValueError(f"The supplied file {root!s} is not a .m3u playlist")
        return [root.resolve()]

    if not root.is_dir():
        raise NotADirectoryError(f"The supplied path {root!s} is neither a file nor a directory")

    # non-recursive glob
    return sorted(p.resolve() for p in root.glob("*.m3u") if p.is_file())

def api_request(session: requests.Session, method: str, endpoint: str, **kwargs) -> requests.Response:
    """
    Perform an HTTP request against the mStream server.

    Parameters
    ----------
    session
        Authenticated `requests.Session`.
    method
        HTTP method (`GET`, `POST` …).
    endpoint
        API endpoint (e.g. `/api/v1/playlist/save`). Leading slash is optional.
    kwargs
        Passed directly to `Session.request` (usually `json=`).

    Returns
    -------
    requests.Response
        The successful response object.

    Raises
    ------
    requests.HTTPError
        If the response status is not 2xx.
    """
    url = f"{Settings.BASE_URL}/{endpoint.lstrip('/')}"
    resp = session.request(method=method, url=url, timeout=30, **kwargs)

    try:
        resp.raise_for_status()
    except requests.HTTPError:
        log.exception(
            "❌ HTTP %s %s → %s: %s",
            method,
            endpoint,
            resp.status_code,
            resp.text,
        )
        raise

    return resp

def login(session: requests.Session) -> None:
    """
    Authenticate and store the CSRF token in the session headers.

    Parameters
    ----------
    session
        Authenticated ``requests.Session``.
    
    Returns
    -------
    Nothing
    """
    payload = {"username": Settings.USERNAME, "password": Settings.PASSWORD}
    resp = api_request(session, "POST", "/api/v1/auth/login", json=payload)
    data = resp.json()
    csrf = data.get("token")
    if csrf:
        session.headers.update({"X-CSRF-Token": csrf})
    else:
        log.info("ℹ️ Login succeeded but no CSRF token was returned. Continuing without the X-CSRF-Token header (most API calls accept this).")
    
def _parse_cli() -> Namespace:
    """
    Argument parsing.

    Parameters
    ----------
    Nothing
    
    Returns
    -------
    List of parameters passed in the CLI
    """
    parser = ArgumentParser(
        description="Add playlists (in m3u format) to an mStream server via its REST API."
    )
    parser.add_argument(
        "-p",
        "--path",
        required=True,
        type=Path,
        help="Path to a .m3u file **or** a directory containing .m3u files (non-recursive).",
    )
    return parser.parse_args()

def main() -> int:
    # Validate config
    try:
        Settings.validate()
    except RuntimeError as exc:
        log.critical("❌ Configuration error: %s", exc)
        return 1

    # Parse arguments
    args = _parse_cli()
    target = args.path.expanduser().resolve()

    # Resolve playlist files
    try:
        m3u_files = gather_m3u_files(target)
    except (FileNotFoundError, ValueError, NotADirectoryError) as exc:
        log.error("❌ %s", exc)
        return 1

    if not m3u_files:
        log.error("❌ No .m3u files found under %s", target)
        return 1

    log.info("🔎 Found %d .m3u file(s) to process.", len(m3u_files))

    # HTTP session + login
    with requests.Session() as session:
        session.headers.update(
            {"Accept": "application/json", "Content-Type": "application/json"}
        )
        try:
            login(session)
        except Exception as exc:  # noqa: BLE001 - surface any login failure
            log.critical("❌ Login failed: %s", exc)
            return 1

        # Upload each playlist
        for m3u_path in m3u_files:
            try:
                songs = parse_m3u(m3u_path)
                playlist_name = m3u_path.stem
                log.info(
                    "▶️ Uploading playlist %s (%d songs)…",
                    playlist_name,
                    len(songs),
                )

                payload = {"title": playlist_name, "songs": songs}
                api_request(session, "POST", "/api/v1/playlist/save", json=payload)

                log.info("✅ %s uploaded successfully.", playlist_name)

            except Exception as exc:  # noqa: BLE001 - keep processing other files
                log.error("❌ Failed to add %s: %s", m3u_path.name, exc)

    log.info("🎉 All done!")
    return 0


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    sys.exit(main())
