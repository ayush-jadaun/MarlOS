# Changelog

All notable changes to MarlOS will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.3] - 2025-01-11

### Fixed
- Fixed `marl install` command crashing when MarlOS is installed via pip
- Fixed installation wizard trying to find `requirements.txt` in site-packages
- Fixed CLI commands failing to detect pip vs source installations properly

### Added
- **PATH Setup Documentation**
  - Added comprehensive PATH setup guide for Windows/Mac/Linux (`docs/PATH_SETUP_QUICK_REFERENCE.md`)
  - Added detailed troubleshooting section to `docs/PIP_INSTALL.md`
  - Added "Installing for Friends" quick guide (`INSTALL_FOR_FRIENDS.md`)

- **Automated Installers**
  - Added Windows PowerShell installer (`scripts/install_windows.ps1`) with automatic PATH setup
  - Added Windows Batch installer (`scripts/install_windows.bat`)
  - Added post-installation checker (`scripts/post_install.py`)

- **Installation Detection**
  - Added `is_pip_installed()` to detect pip vs source installations
  - Added `get_source_root()` to find source directory for development
  - CLI now provides appropriate guidance based on installation type

- **Source Code Management** ⭐ NEW
  - Added `check_source_required()` to detect if source code is available
  - Added `clone_repository()` for interactive repository cloning
  - CLI now offers to clone repository automatically when needed
  - Smart detection of existing repositories with update option
  - Automatic editable installation after cloning

- **Agent Running Detection** ⭐ NEW
  - Added `check_agent_running()` to detect if MarlOS agent is active
  - Added `prompt_start_agent()` with helpful start instructions
  - All commands now check if agent is running before execution
  - Clear error messages when agent is not running
  - Offers to start agent interactively when needed

### Changed
- Updated `marl install` to show success message for pip installations instead of crashing
- Updated all start commands to detect and handle pip installations properly
- Updated configuration and documentation menus to work with both installation types
- CLI now guides users to clone source code when needed for running nodes
- Improved error messages throughout with actionable next steps
- **All commands now check prerequisites before execution** ⭐
  - `marl start` checks for source code, offers to clone
  - `marl execute`, `marl status`, `marl peers`, `marl wallet`, `marl watch`, `marl submit` check if agent is running
  - Interactive menu shows source code status
  - Clear, helpful messages when requirements not met

### Documentation
- Updated README.md with prominent PATH setup warning
- Added "Installing for Friends" section to README
- Created comprehensive fix summary (`FIX_SUMMARY.md`)
- Created installation improvements summary (`INSTALLATION_IMPROVEMENTS_SUMMARY.md`)

## [1.0.1] - 2025-01-09

### Added
- Published to PyPI for easier installation
- Added pip installation support

### Changed
- Updated packaging configuration for PyPI

## [1.0.0] - 2025-01-08

### Added
- Initial release
- Multi-agent reinforcement learning operating system
- Decentralized P2P architecture using ZeroMQ
- Fairness-aware economic layer with MarlCredits
- RL-based job bidding and allocation
- Interactive CLI with `marl` command
- Docker Compose support for local testing
- Distributed deployment capabilities
- Web dashboard for monitoring
- Support for shell, Docker, and security scanning jobs
- Self-healing and fault tolerance
- Cryptographic authentication with Ed25519
- Comprehensive documentation

### Core Features
- Autonomous distributed computing without centralized orchestrator
- PPO-based decision making for job allocation
- Trust and reputation system
- Progressive taxation and UBI mechanisms
- Speculative execution for zero-latency responses
- Quorum consensus for consistency
- Deterministic coordinator election

---

## Legend
- **Added** for new features
- **Changed** for changes in existing functionality
- **Deprecated** for soon-to-be removed features
- **Removed** for now removed features
- **Fixed** for any bug fixes
- **Security** for vulnerability fixes

## Links
- [GitHub Repository](https://github.com/ayush-jadaun/MarlOS)
- [Issue Tracker](https://github.com/ayush-jadaun/MarlOS/issues)
- [Documentation](https://github.com/ayush-jadaun/MarlOS/blob/main/README.md)
