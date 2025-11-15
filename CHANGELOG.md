# Changelog

All notable changes to MarlOS will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.5/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.5] - 2025-11-15 ⭐ CONFIGURATION SYSTEM UPDATE

### 🎉 Revolutionary Change: Production-Grade Two-Tier Configuration

**MarlOS now features a sophisticated configuration management system!**

Previously, configuration was scattered across environment variables and temporary files.
Now with v1.0.5, you get a **production-ready two-tier system**:

1. **System Defaults** - Built-in sensible defaults (agent/config.py)
2. **Per-Node Configuration** - Individual node configs (~/.marlos/nodes/{node_id}/config.json)
3. **Environment Overrides** - Temporary overrides via environment variables

### Added
- **Two-Tier Configuration System** ⭐
  - Created `agent/node_config.py` for node configuration management
  - Per-node config files at `~/.marlos/nodes/{node_id}/config.json`
  - Configuration precedence: Environment > Node Config > System Defaults
  - Support for multiple network modes (Private/Public)
  - DHT configuration for cross-internet discovery

- **Node Management Commands** 🔧
  - `marl nodes list` - List all configured nodes
  - `marl nodes show <node_id>` - Display node configuration
  - `marl nodes edit <node_id>` - Edit node config in default editor
  - `marl nodes delete <node_id>` - Remove node configuration

- **Improved Network Configuration** 🌐
  - Private Mode: Manual peer management for personal networks
  - Public Mode: DHT-based automatic discovery
  - Network mode selection during node creation
  - Bootstrap peers configuration per node
  - Dynamic peer management

- **Comprehensive Documentation** 📚
  - Created `docs/CONFIG_ARCHITECTURE.md` - System design documentation
  - Created `docs/CONFIG_MANAGEMENT_GUIDE.md` - Node management guide
  - Created `docs/FULL_CONFIG_USAGE.md` - Complete configuration reference
  - Created `docs/USER_GUIDE_NETWORK_MODES.md` - Network modes user guide
  - Created `docs/CROSS_INTERNET_DISCOVERY.md` - Cross-network connectivity guide
  - Created `docs/README.md` - Documentation index
  - Updated `docs/COMMANDS.md` with node management commands

### Changed
- **Updated Configuration Loader** (`agent/config.py`)
  - Rewritten `load_config()` to support three-tier precedence
  - Automatic node config file detection based on NODE_ID
  - Improved error handling and fallbacks
  - Support for both JSON node configs and environment variables

- **Simplified Node Creation** (`cli/main.py`)
  - Node creation now generates persistent config files
  - Launch scripts simplified to only need NODE_ID
  - All settings loaded from node config automatically
  - Better network mode selection during setup

- **Updated Launch Scripts**
  - `scripts/start-node.sh` - Simplified to use node configs
  - `scripts/start-node.bat` - Windows version updated
  - Only requires NODE_ID environment variable
  - All other settings loaded from config file

- **Documentation Cleanup** 🧹
  - Removed 7 redundant/outdated documentation files
  - Reorganized guides into docs/ folder
  - Created comprehensive documentation index
  - Updated README with new config documentation links

### Removed
- Deleted redundant summary files (COMPLETE_FIX_SUMMARY.md, FINAL_UPDATE_SUMMARY.md, etc.)
- Removed implementation planning documents
- Cleaned up outdated guides folder

### Migration Guide

**For Users:**
- **Before**: Configure everything via environment variables
- **After**: Create nodes with `marl start`, configs saved automatically
- **Managing Nodes**: Use `marl nodes` commands to manage configurations
- **Updating**: Run `pip install --upgrade marlos`

**For Developers:**
- Node configs stored in `~/.marlos/nodes/{node_id}/config.json`
- Environment variables still work as overrides
- Use `node_config` module for programmatic access

### Benefits
1. **Persistent Configuration** - Node settings saved and reused
2. **Easy Multi-Node Management** - Run multiple nodes with different configs
3. **Clear Configuration Hierarchy** - Understand precedence easily
4. **Better Organization** - Per-node configs instead of scattered env vars
5. **Network Mode Support** - Private and Public modes with proper config
6. **Production Ready** - Scalable configuration for real deployments

## [1.0.5] - 2025-01-12 ⭐ MAJOR UPDATE

### 🎉 Revolutionary Change: Complete Package Distribution

**MarlOS is now a complete, self-contained package!**

Previously, users had to:
1. `pip install marlos` (get CLI only)
2. Manually clone the GitHub repository (get agent code)
3. Set up environment and dependencies

Now with v1.0.5, a single command gives you **EVERYTHING**:
```bash
pip install marlos
```

This includes:
- ✅ CLI tool (`marl` command)
- ✅ Complete agent code
- ✅ RL trainer modules
- ✅ Hardware integration code (Arduino, ESP)
- ✅ Configuration files
- ✅ Scripts and examples
- ✅ ALL necessary components to run nodes immediately

### Added
- **Complete Package Distribution**
  - All source code now included in pip package
  - Added `config/`, `hardware/`, `scripts/`, `examples/` as Python packages
  - Updated `MANIFEST.in` to include all non-Python files (Arduino .ino, configs, scripts)
  - Updated `setup.py` and `pyproject.toml` to package all components
  - Added `__init__.py` to data directories for proper packaging

- **Improved Installation Detection**
  - Completely rewritten `get_source_root()` to work with pip installations
  - Now detects installed package location using `pkg_resources`
  - Works seamlessly for both pip install and development mode
  - Added 4 fallback methods to find installation location

### Changed
- **Simplified CLI Logic**
  - Replaced `check_source_required()` with simpler `verify_installation()`
  - Removed complex repository cloning logic (no longer needed!)
  - CLI now uses installed package location automatically
  - No more "source code not found" errors for pip installations

### Removed
- **Repository Cloning Feature**
  - Removed `clone_repository()` function (no longer needed)
  - Removed interactive git clone prompts
  - Source code is now always available via pip installation

### Migration Guide

**For Users:**
- **Before**: `pip install marlos` → manually clone repo → setup
- **After**: `pip install marlos` → ready to go!
- **Updating**: Just run `pip install --upgrade marlos`

**For Developers:**
- Use `pip install -e .` for development (editable mode)
- Use `pip install git+https://github.com/ayush-jadaun/MarlOS.git` for testing
- No need to publish to PyPI for every test

### Benefits
1. **One-Step Installation** - No manual cloning required
2. **Automatic Updates** - `pip install --upgrade marlos` updates everything
3. **No Git Required** - Users don't need Git installed
4. **Consistent Experience** - Same installation process for everyone
5. **Simpler Testing** - Test via GitHub without PyPI publishing
6. **Smaller Learning Curve** - Standard pip workflow

## [1.0.5] - 2025-01-11

### Fixed
- Fixed `marl install` command crashing when MarlOS is installed via pip
- Fixed installation wizard trying to find `requirements.txt` in site-packages
- Fixed CLI commands failing to detect pip vs source installations properly
- **Fixed Windows native mode launch script error** - Now creates `.bat` files on Windows instead of `.sh` files
- Fixed script execution on Windows (added `shell=True` for batch files)

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

## [1.0.5] - 2025-01-09

### Added
- Published to PyPI for easier installation
- Added pip installation support

### Changed
- Updated packaging configuration for PyPI

## [1.0.5] - 2025-01-08

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
