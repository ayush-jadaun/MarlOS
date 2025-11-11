# Source Code and Agent Running Checks - Feature Documentation

## Overview

MarlOS CLI now intelligently checks for:
1. **Source code availability** - Required to start nodes
2. **Agent running status** - Required to execute commands

This ensures users get helpful guidance instead of cryptic errors.

---

## New Features

### 1. Automatic Source Code Detection

The CLI now detects if the full source code is installed and offers to clone it if needed.

**Before**:
```bash
$ marl start
Error: agent/main.py not found
```

**After**:
```bash
$ marl start

⚠️  MarlOS Source Code Required

To start MarlOS nodes, you need the full source code.

✓ MarlOS CLI is installed via pip
✗ But agent source code is not available

How to Install Source Code:

Option 1 - Clone from GitHub (Recommended):
  git clone https://github.com/ayush-jadaun/MarlOS.git
  cd MarlOS
  pip install -e .

Option 2 - Download ZIP:
  1. Visit: https://github.com/ayush-jadaun/MarlOS
  2. Click 'Code' → 'Download ZIP'
  3. Extract and run: pip install -e .

Do you want me to clone the repository now? [Y/n]:
```

---

### 2. Interactive Repository Cloning

If user agrees, the CLI can clone the repository automatically:

```bash
$ marl start

Do you want me to clone the repository now? [Y/n]: y

📦 Cloning MarlOS Repository

✓ Git is installed

Where to clone MarlOS? [/home/user/MarlOS]:

Cloning to /home/user/MarlOS...

✓ Cloned successfully to /home/user/MarlOS

Install in editable mode (pip install -e .)? [Y/n]: y

Installing in editable mode...

✓ Installed in editable mode!

You're all set! Source code is ready.
```

**Features**:
- Checks if Git is installed
- Asks where to clone (defaults to ~/MarlOS)
- Handles existing directories (offers to pull updates)
- Offers to install in editable mode
- Verifies installation success

---

### 3. Agent Running Detection

All commands that need a running agent now check first:

```bash
$ marl status

⚠️  MarlOS Agent Not Running

The MarlOS agent must be running to use this command.

How to Start MarlOS:

Option 1 - Interactive:
  marl start

Option 2 - Direct:
  cd ~/MarlOS  # or your MarlOS directory
  python -m agent.main

Option 3 - Docker:
  cd ~/MarlOS
  docker-compose up -d

Do you want to start MarlOS now? [Y/n]:
```

**Commands with agent check**:
- ✅ `marl execute`
- ✅ `marl status`
- ✅ `marl peers`
- ✅ `marl wallet`
- ✅ `marl watch`
- ✅ `marl submit`
- ✅ All interactive menu options

---

### 4. Smart Installation Status

The main menu shows clear status:

```bash
╔═══════════════════════════════════════════════════════════════╗
║                       MarlOS v1.0.4                           ║
╚═══════════════════════════════════════════════════════════════╝

ℹ️  Note: MarlOS CLI is installed but source code is not available.
   You can use CLI commands, but to start nodes you'll need the source.

┌──────────────────────────────────────────────────────────┐
│ Option │ Description                                     │
├──────────────────────────────────────────────────────────┤
│ 1      │ 🚀 Start MarlOS (choose mode)                  │
│ 2      │ ⚡ Quick Execute (run a command)               │
...
```

---

## Technical Implementation

### New Helper Functions

```python
def check_source_required():
    """Check if source code is required and prompt user to install if not present"""
    # Returns True if source available, False otherwise
    # Offers to clone if missing

def clone_repository():
    """Clone MarlOS repository interactively"""
    # Handles git clone with user interaction
    # Offers editable install
    # Updates existing repos

def check_agent_running(port=3001):
    """Check if MarlOS agent is running on specified port"""
    # Uses socket connection test
    # Returns True/False

def prompt_start_agent():
    """Prompt user to start agent if not running"""
    # Shows helpful start instructions
    # Asks if user wants to start now
```

---

## User Workflows

### Workflow 1: Fresh Install (pip only)

```bash
# User installs via pip
pip install git+https://github.com/ayush-jadaun/MarlOS.git

# User tries to start
marl start

# CLI detects no source, offers to clone
⚠️  MarlOS Source Code Required
Do you want me to clone the repository now? [Y/n]: y

# CLI clones and installs
✓ Cloned successfully
✓ Installed in editable mode!

# User can now start
marl start
# [Shows mode selection menu]
```

---

### Workflow 2: Execute Without Agent Running

```bash
# User tries to execute command
marl execute "echo hello"

# CLI detects agent not running
⚠️  MarlOS Agent Not Running
Do you want to start MarlOS now? [Y/n]: y

# CLI launches start menu
# User selects mode and starts agent
# Then can execute command
```

---

### Workflow 3: Check Status Before Starting

```bash
# User checks status
marl status

# CLI detects agent not running
✗ No MarlOS agent running on port 3001

Start MarlOS first:
  marl start

# Clear, actionable guidance!
```

---

## Configuration

### Default Paths Searched

The CLI automatically searches for source code in:
- Current working directory
- `~/MarlOS`
- `~/Documents/MarlOS`
- `/opt/MarlOS` (Linux) or `C:/MarlOS` (Windows)

### Default Clone Location

```python
default_path = Path.home() / "MarlOS"
```

User can override during clone prompt.

---

## Error Handling

### Git Not Installed

```bash
✗ Git is not installed!

Install Git first:
  https://git-scm.com/downloads
```

### Directory Already Exists

```bash
⚠️ MarlOS already cloned at /home/user/MarlOS

Pull latest changes? [Y/n]:
```

### Clone Failed

```bash
✗ Clone failed: Permission denied

# Shows error and suggests manual clone
```

---

## Benefits

### For Users

✅ **Clear Guidance** - No cryptic errors
✅ **Automatic Setup** - CLI can clone for them
✅ **Smart Detection** - Knows what's missing
✅ **Helpful Messages** - Shows exact commands
✅ **Interactive** - Offers to fix issues

### For Developers

✅ **Better UX** - Users don't get stuck
✅ **Less Support** - Self-service installation
✅ **Clear Separation** - CLI vs Agent requirements
✅ **Flexible** - Works with pip or source installs

---

## Testing

### Test Source Detection

```bash
# Test 1: No source
pip install git+https://github.com/ayush-jadaun/MarlOS.git
marl start
# Should prompt to clone

# Test 2: Source exists
cd ~/MarlOS
marl start
# Should show mode selection

# Test 3: Auto-clone
marl start
# Accept clone prompt
# Should successfully clone and install
```

### Test Agent Detection

```bash
# Test 1: No agent running
marl status
# Should show "not running" message

# Test 2: Agent running
# Start agent in background
marl status
# Should show actual status

# Test 3: Wrong port
marl status --port 9999
# Should detect no agent on that port
```

---

## Future Enhancements

Possible improvements:
- [ ] Auto-start agent in background
- [ ] Remember last used port
- [ ] Check for updates on clone
- [ ] Support multiple source locations
- [ ] Cache detection results
- [ ] Health check endpoint instead of socket test

---

## Backwards Compatibility

✅ **Fully Compatible** - All existing commands work
✅ **No Breaking Changes** - Only adds helpful checks
✅ **Optional Prompts** - Users can say "no" and continue manually

---

## Version

**Added in**: v1.0.4
**Status**: ✅ Production Ready
**Breaking Changes**: None

---

**Summary**: The CLI now guides users through installation and checks requirements before commands, making MarlOS much easier to use!
