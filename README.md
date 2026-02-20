# mstream_add_playlist

> **Add one or many `.m3u` playlists to an mStream server via its public REST API.**
> The script is completely self‑contained, configurable through environment variables
> (or a `.env` file) and ships with sensible logging and validation.

---

## Table of Contents

- [mstream\_add\_playlist](#mstream_add_playlist)
  - [Table of Contents](#table-of-contents)
  - [Features](#features)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
    - [From source (recommended)](#from-source-recommended)
      - [1. Clone the repo (or copy the single file into a folder of your choice)](#1-clone-the-repo-or-copy-the-single-file-into-a-folder-of-your-choice)
      - [2. Create a virtual environment (optional but clean)](#2-create-a-virtual-environment-optional-but-clean)
      - [3. Install the required third‑party libraries](#3-install-the-required-thirdparty-libraries)
    - [As a one‑liner (if you only need the script)](#as-a-oneliner-if-you-only-need-the-script)
  - [Configuration](#configuration)
    - [Using environment variables](#using-environment-variables)
    - [Using a .env file](#using-a-env-file)
  - [Usage](#usage)
    - [Add a single playlist](#add-a-single-playlist)
    - [Add every .m3u in a directory (non‑recursive)](#add-every-m3u-in-a-directory-nonrecursive)
    - [CLI help](#cli-help)
  - [Logging](#logging)
  - [Error handling \& exit codes](#error-handling--exit-codes)
  - [License](#license)

---

## Features

| ✅ | Description |
| :--- | :-------------- |
| Environment aware | Reads `MS_BASE_URL`, `MS_USERNAME`, `MS_PASSWORD` from the environment or from a `.env` file placed next to the script. |
| Configuration validation | Fails fast with a clear message if any required value is missing or empty. |
| Single‑file or bulk mode | Accepts a single `.m3u` file or a directory (non‑recursive) containing many playlists. |
| Robust HTTP handling | Uses `requests.Session`, adds the CSRF token automatically and logs HTTP errors with a stack trace. |
| Typed & unit‑testable | All public functions are annotated (`List[str]`, `Path`, …) – easy to mock in tests. |
| Adjustable verbosity | Set `PYTHON_LOGGING=DEBUG\|INFO\|WARNING\|ERROR\|CRITICAL` to control console output. |
| Zero‑dependency runtime | Apart from `requests` and `python-dotenv`, everything is from the Python std‑lib. |

---

## Prerequisites

- Python 3.8+ (typing `Final` is built‑in from 3.8 onward)
- Access to an mStream server with a user that can call the REST API (default `admin:admin` works on a fresh install).

---

## Installation

### From source (recommended)

#### 1. Clone the repo (or copy the single file into a folder of your choice)

```text
git clone https://github.com/your‑org/mstream_add_playlist.git
cd mstream_add_playlist
```

#### 2. Create a virtual environment (optional but clean)

```text
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
```

#### 3. Install the required third‑party libraries

```bash
pip install -r requirements.txt
```

### As a one‑liner (if you only need the script)

```bash
pip install requests python-dotenv
```

Then copy the mstream_add_playlist.py file to a location in your $PATH or run it directly with ```python -m```.

## Configuration

### Using environment variables

The script looks for three environment variables. They can be supplied in any of the following ways:

| Variable | Meaning | Default (if not provided) |
| :---------- | :--------- | :--------------------------- |
| MS_BASE_URL | Base URL of the mStream API (e.g. `http://127.0.0.1:3000`) | `http://127.0.0.1:3000` |
| MS_USERNAME | Username for authentication | admin |
| MS_PASSWORD | Password for authentication | admin |
| PYTHON_LOGGING | Logging level (DEBUG, INFO, …) – optional | INFO |

### Using a .env file

Place a file named .env next to the script (same directory) with contents such as:

```text
MS_BASE_URL=http://my-mstream.example.com:3000
MS_USERNAME=myuser
MS_PASSWORD=supersecret
PYTHON_LOGGING=DEBUG        # optional, makes the script chatter
```

The python-dotenv package will automatically load these values before any validation occurs.

## Usage

>All examples assume the script lives in a package called mstream_add_playlist.
>If you kept the file as a plain script, replace python -m mstream_add_playlist with python mstream_add_playlist.py.

### Add a single playlist

```bash
python -m mstream_add_playlist -p /path/to/playlist.m3u
```

### Add every .m3u in a directory (non‑recursive)

```bash
python -m mstream_add_playlist -p /path/to/playlists/```
```

### CLI help

```bash
python -m mstream_add_playlist -h


usage: python -m mstream_add_playlist [-h] -p PATH

Add playlists (in m3u format) to an mStream server via its REST API.

optional arguments:
  -h, --help            show this help message and exit
  -p PATH, --path PATH  Path to a .m3u file or a directory containing .m3u
                        files (non-recursive).
```

## Logging

The script writes to stdout using the built‑in logging module.

| Environment variable | Effect |
| :-------------------- | :------ |
| PYTHON_LOGGING=DEBUG | Shows every HTTP request/response, file parsing, etc. |
| PYTHON_LOGGING=INFO (default) | Shows high‑level progress (files found, uploads succeeded/failed). |
| PYTHON_LOGGING=WARNING | Only warns about missing files or HTTP problems. |
| PYTHON_LOGGING=ERROR or CRITICAL | Silent on success, only prints fatal errors. |

You can redirect output to a file if you wish:

```bash
python -m mstream_add_playlist -p ./myplaylists > import.log 2>&1
```

## Error handling & exit codes

| Exit code | Meaning |
| :--------- | :------- |
| 0 | All playlists processed successfully. |
| 1 | Configuration missing/invalid or argument parsing failed or any unrecoverable runtime error (e.g. login failure, HTTP error that aborts the whole run). |

When an individual playlist fails (e.g. malformed .m3u or HTTP 409), the script logs the error but continues with the remaining files, finally exiting with 0 only if no fatal error occurred.

## License

This project is released under the GNU General Public License v3.0 – feel free to copy, modify, and distribute it, provided you retain the license notice.
