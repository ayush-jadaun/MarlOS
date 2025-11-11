# Install MarlOS via pip

## 🚀 Quick Installation

### Option 1: Install from PyPI (Once Published)

```bash
pip install marlos
```

### Option 2: Install from GitHub (Current)

```bash
pip install git+https://github.com/ayush-jadaun/MarlOS.git
```

### Option 3: Install from Local Clone

```bash
git clone https://github.com/ayush-jadaun/MarlOS.git
cd MarlOS
pip install -e .  # Editable install for development
```

---

## ✨ Using the `marl` Command

After installation, the `marl` command is available globally:

### Interactive Mode (Recommended)

Simply type:
```bash
marl
```

This launches the beautiful interactive menu:

```
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   ███╗   ███╗ █████╗ ██████╗ ██╗      ██████╗ ███████╗      ║
║   ████╗ ████║██╔══██╗██╔══██╗██║     ██╔═══██╗██╔════╝      ║
║   ██╔████╔██║███████║██████╔╝██║     ██║   ██║███████╗      ║
║   ██║╚██╔╝██║██╔══██║██╔══██╗██║     ██║   ██║╚════██║      ║
║   ██║ ╚═╝ ██║██║  ██║██║  ██║███████╗╚██████╔╝███████║      ║
║   ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚══════╝      ║
║                                                               ║
║        Autonomous Distributed Computing OS                   ║
║        v1.0.0 | Team async_await                             ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝

┌──────────────────────────────────────────────────────────┐
│ Option │ Description                                     │
├──────────────────────────────────────────────────────────┤
│ 1      │ 🚀 Start MarlOS (choose mode)                  │
│ 2      │ ⚡ Quick Execute (run a command)               │
│ 3      │ 📊 Check Status                                │
│ 4      │ 👥 List Peers                                  │
│ 5      │ 💰 View Wallet                                 │
│ 6      │ 📺 Live Monitor                                │
│ 7      │ 📝 Create Job                                  │
│ 8      │ 📤 Submit Job                                  │
│ 9      │ ⚙️  Configuration                              │
│ 10     │ 📖 Documentation                               │
│ 0      │ ❌ Exit                                        │
└──────────────────────────────────────────────────────────┘

Select an option [1]: _
```

### Direct Commands

Use specific commands directly:

```bash
# Start MarlOS (interactive mode selection)
marl start

# Run installation wizard
marl install

# Quick execute a command
marl execute "echo Hello MarlOS"

# Check status
marl status

# List peers
marl peers

# View wallet
marl wallet

# Live monitoring
marl watch

# Create job template
marl create --name shell --command "echo test"

# Submit job
marl submit job.json

# Show version
marl version

# Show help
marl --help
```

---

## 📋 Complete Workflow

### 1. Install MarlOS

```bash
pip install git+https://github.com/ayush-jadaun/MarlOS.git
```

### 2. First-Time Setup

Run the interactive menu:
```bash
marl
```

Or run the installation wizard directly:
```bash
marl install
```

**The wizard will:**
- ✅ Check dependencies
- ✅ Create virtual environment
- ✅ Install Python packages
- ✅ Set up configuration

### 3. Choose Your Mode

From the interactive menu, select **Option 1: Start MarlOS**

Then choose:
- **Docker**: For local testing with multiple nodes
- **Native**: For real distributed deployment
- **Development**: For debugging

### 4. Start Your Node

**Docker Mode:**
```bash
marl start
# Select: 1 (Docker)
# Automatically starts 3 agent nodes
```

**Native Mode:**
```bash
marl start
# Select: 2 (Native)
# Configure node ID and bootstrap peers
# Launch script is created automatically
```

**Quick Dev Mode:**
```bash
marl start
# Select: 3 (Development)
# Starts immediately with debug logging
```

### 5. Submit Jobs

**Quick execute:**
```bash
marl execute "echo Hello from MarlOS"
marl execute "python --version"
marl execute "curl https://api.github.com"
```

**Create and submit custom jobs:**
```bash
# Create template
marl create --name shell --command "ls -la" --output my-job.json

# Submit
marl submit my-job.json
```

### 6. Monitor

**Check status:**
```bash
marl status
```

**Watch live:**
```bash
marl watch
```

**View peers:**
```bash
marl peers
```

**Check wallet:**
```bash
marl wallet
```

---

## 🌐 Network Deployment Example

### Coordinator Machine

```bash
# Install
pip install git+https://github.com/ayush-jadaun/MarlOS.git

# Start
marl start
# Choose: Native Mode
# Node ID: coordinator
# Bootstrap Peers: (leave empty for coordinator)

# Note your IP
ip addr show
# Example: 192.168.1.100
```

### Worker Machines (1, 2, 3...)

On each worker:

```bash
# Install
pip install git+https://github.com/ayush-jadaun/MarlOS.git

# Start
marl start
# Choose: Native Mode
# Node ID: worker-1 (unique for each)
# Bootstrap Peers: 192.168.1.100 (coordinator IP)
```

### Submit Jobs from Any Machine

```bash
marl execute "echo Hello from the swarm!" --port 3001
```

The job automatically:
- ✅ Broadcasts to all nodes
- ✅ RL-based auction determines best executor
- ✅ Executes on optimal node
- ✅ Results returned to all nodes

---

## 💡 Pro Tips

### 1. Set Default Port

```bash
export MARLOS_PORT=3001
marl status  # Uses port 3001 by default
```

### 2. Shell Alias

Add to `~/.bashrc` or `~/.zshrc`:

```bash
alias ms='marl status'
alias mx='marl execute'
alias mw='marl watch'
```

Then use:
```bash
ms              # Check status
mx "echo test"  # Execute command
mw              # Watch live
```

### 3. Background Service

For always-on nodes:

```bash
marl start
# Choose: Background Service
# Automatically creates systemd service (Linux)
```

Manage with:
```bash
sudo systemctl start marlos-node
sudo systemctl stop marlos-node
sudo systemctl status marlos-node
journalctl -u marlos-node -f
```

### 4. Configuration Files

MarlOS looks for config in:
- `./agent-config.yml` (current directory)
- `~/.marlos/config.yml` (user config)
- `/etc/marlos/config.yml` (system config)

Create your own:
```yaml
node:
  id: my-custom-node
  name: Production Node 1

network:
  pub_port: 5555
  sub_port: 5556
  bootstrap_peers:
    - tcp://192.168.1.100:5555
    - tcp://192.168.1.101:5555

executor:
  max_concurrent_jobs: 5
  docker_enabled: true

dashboard:
  port: 3001
  host: 0.0.0.0
```

Then start with custom config:
```bash
marl start --config ~/.marlos/config.yml
```

---

## 🔧 Development Mode

### Editable Installation

For development/contribution:

```bash
git clone https://github.com/ayush-jadaun/MarlOS.git
cd MarlOS
pip install -e .  # Editable install
```

Changes to the code immediately reflected in `marl` command!

### Run Tests

```bash
cd MarlOS
./test_deployment.sh
```

### Debug Mode

```bash
export LOG_LEVEL=DEBUG
marl start
# Choose: Development Mode
```

---

## 📦 What Gets Installed

### Global Command

- `marl` - Main CLI entry point

### Python Packages

All dependencies from `requirements.txt`:
- `click` - CLI framework
- `rich` - Beautiful terminal output
- `zeromq` - P2P networking
- `torch` - RL models
- `stable-baselines3` - RL algorithms
- And more...

### No System Modifications

- ✅ Pure Python installation
- ✅ No system services (unless explicitly created)
- ✅ No firewall changes (unless explicitly approved)
- ✅ User-level installation

---

## 🗑️ Uninstallation

### Remove pip Package

```bash
pip uninstall marlos
```

### Remove Data (Optional)

```bash
rm -rf ~/.marlos
rm -rf ~/MarlOS  # If you cloned the repo
```

### Remove System Service (If Created)

```bash
sudo systemctl stop marlos-*
sudo systemctl disable marlos-*
sudo rm /etc/systemd/system/marlos-*.service
sudo systemctl daemon-reload
```

---

## 🆘 Troubleshooting

### "marl: command not found"

This is the most common issue! When you install a Python package with pip, it places executable scripts in a specific directory. If that directory isn't in your system's PATH, the `marl` command won't be found.

**Quick Test:**
```bash
# Try to find where marl was installed
pip show -f marlos | grep marl
# or
which marl  # Linux/Mac
where marl  # Windows
```

---

### 📍 Adding Python Scripts to PATH - Complete Guide

#### Why This Happens
- **pip doesn't modify your PATH** - it only installs to a directory
- **Python installer's job** - the "Add to PATH" checkbox during Python installation
- Different operating systems have different default script directories

---

#### 🪟 Windows - Detailed Instructions

**Option 1: Reinstall Python with PATH (Recommended)**

1. Download Python from https://python.org
2. Run installer
3. ✅ **CHECK** "Add Python to PATH" (very important!)
4. Click "Install Now"
5. Restart terminal/PowerShell
6. Reinstall marlos: `pip install marlos`

**Option 2: Manually Add to PATH**

1. **Find your Python Scripts directory:**
   ```powershell
   # Run this in PowerShell
   python -c "import sys; print(sys.prefix + '\\Scripts')"
   # Example output: C:\Users\YourName\AppData\Local\Programs\Python\Python311\Scripts
   ```

2. **Add to PATH via GUI:**
   - Press `Windows + R`, type `sysdm.cpl`, press Enter
   - Go to "Advanced" tab → "Environment Variables"
   - Under "User variables", find and select "Path"
   - Click "Edit" → "New"
   - Paste your Scripts directory path
   - Click "OK" on all windows
   - **Restart your terminal/PowerShell**

3. **Or add via PowerShell (run as Administrator):**
   ```powershell
   # Replace with your actual path from step 1
   $scriptsPath = "C:\Users\YourName\AppData\Local\Programs\Python\Python311\Scripts"
   [Environment]::SetEnvironmentVariable("Path", $env:Path + ";$scriptsPath", "User")
   ```

4. **Verify:**
   ```powershell
   # Close and reopen PowerShell/CMD
   marl --help
   ```

**Option 3: Use `python -m` (no PATH changes needed)**
```bash
python -m cli.main
python -m cli.main status
python -m cli.main execute "echo test"
```

---

#### 🐧 Linux - Detailed Instructions

**Option 1: Add ~/.local/bin to PATH (Recommended)**

When you run `pip install --user marlos`, scripts go to `~/.local/bin`

1. **Edit your shell config file:**
   ```bash
   # For bash users
   nano ~/.bashrc

   # For zsh users (macOS default on newer versions)
   nano ~/.zshrc

   # For fish users
   nano ~/.config/fish/config.fish
   ```

2. **Add this line at the end:**
   ```bash
   # For bash/zsh
   export PATH="$HOME/.local/bin:$PATH"

   # For fish
   set -gx PATH $HOME/.local/bin $PATH
   ```

3. **Reload your shell config:**
   ```bash
   # For bash
   source ~/.bashrc

   # For zsh
   source ~/.zshrc

   # For fish
   source ~/.config/fish/config.fish

   # Or just close and reopen your terminal
   ```

4. **Verify:**
   ```bash
   which marl
   # Should show: /home/yourname/.local/bin/marl

   marl --help
   ```

**Option 2: System-wide Installation (requires sudo)**
```bash
# Install globally (not recommended, but works)
sudo pip install marlos

# Scripts go to /usr/local/bin (usually already in PATH)
which marl  # Should show: /usr/local/bin/marl
```

**Option 3: Use pipx (Recommended for CLI tools)**
```bash
# Install pipx
python3 -m pip install --user pipx
python3 -m pipx ensurepath  # Automatically adds to PATH!

# Install marlos with pipx
pipx install marlos
# or from git
pipx install git+https://github.com/ayush-jadaun/MarlOS.git

marl --help  # Should work immediately
```

---

#### 🍎 macOS - Detailed Instructions

**Option 1: Add to PATH (Recommended)**

1. **Check your shell:**
   ```bash
   echo $SHELL
   # Output: /bin/bash or /bin/zsh
   ```

2. **Edit config file:**
   ```bash
   # For bash
   nano ~/.bash_profile

   # For zsh (default on macOS Catalina+)
   nano ~/.zshrc
   ```

3. **Add this line:**
   ```bash
   export PATH="$HOME/Library/Python/3.11/bin:$PATH"
   # Note: Change 3.11 to your Python version
   ```

4. **Find your exact Python version:**
   ```bash
   python3 --version
   # Python 3.11.5 → use 3.11
   ```

5. **Reload shell:**
   ```bash
   source ~/.zshrc  # or ~/.bash_profile
   ```

6. **Verify:**
   ```bash
   which marl
   marl --help
   ```

**Option 2: Use Homebrew Python**
```bash
# Install Python via Homebrew
brew install python3

# Homebrew Python automatically sets up PATH
pip3 install marlos

marl --help  # Should work
```

**Option 3: Use pipx**
```bash
brew install pipx
pipx ensurepath  # Adds to PATH automatically
pipx install marlos

marl --help
```

---

#### ✅ Verification Checklist

After adding to PATH, verify everything works:

```bash
# 1. Check if marl is found
which marl       # Linux/Mac
where marl       # Windows

# 2. Check version
marl version

# 3. Run help
marl --help

# 4. Quick test
marl execute "echo Hello MarlOS"
```

---

#### 🔧 Alternative: Use pipx (Best for CLI Tools)

pipx is designed specifically for installing Python CLI applications and automatically handles PATH:

```bash
# Install pipx
pip install pipx

# Let pipx set up PATH (one-time)
pipx ensurepath

# Close and reopen terminal

# Install marlos
pipx install marlos
# or from GitHub
pipx install git+https://github.com/ayush-jadaun/MarlOS.git

# Done! No PATH issues ever again
marl --help
```

**Why pipx is better for CLI tools:**
- ✅ Automatically adds to PATH
- ✅ Isolated environments (no dependency conflicts)
- ✅ Easy upgrades: `pipx upgrade marlos`
- ✅ Easy uninstall: `pipx uninstall marlos`
- ✅ List all installed tools: `pipx list`

---

**Solution 2:** Use python -m (no PATH changes needed):
```bash
python -m cli.main
```

### "ModuleNotFoundError: No module named 'agent'"

You're not in the MarlOS directory. Either:

**Option 1:** Navigate to MarlOS dir:
```bash
cd ~/MarlOS  # Or wherever you cloned it
marl
```

**Option 2:** Use absolute imports (already configured in setup.py)

### "Permission denied" errors

Use virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install marlos
marl
```

### Port already in use

Change default port:
```bash
marl status --port 3002
marl execute "echo test" --port 3002
```

Or in config:
```yaml
dashboard:
  port: 3002
```

---

## 🌟 Why Use pip Installation?

✅ **Global Access**: `marl` command available anywhere
✅ **Clean Installation**: No manual setup needed
✅ **Easy Updates**: `pip install --upgrade marlos`
✅ **Standard Practice**: Like any professional CLI tool
✅ **Virtual Env Support**: Works with venv, conda, etc.
✅ **Beautiful UI**: Rich interactive terminal interface
✅ **Industry Standard**: pip is the standard Python package manager

---

## 📚 Next Steps

After installation:

1. **Quick Test**: `marl execute "echo Hello MarlOS"`
2. **Start Network**: `marl start`
3. **Read Docs**: `marl` → Option 10 (Documentation)
4. **Join Community**: https://github.com/ayush-jadaun/MarlOS

---

## 🤝 Publishing to PyPI

For maintainers to publish to PyPI:

```bash
# Build package
python setup.py sdist bdist_wheel

# Upload to TestPyPI (testing)
twine upload --repository testpypi dist/*

# Test installation
pip install --index-url https://test.pypi.org/simple/ marlos

# Upload to PyPI (production)
twine upload dist/*
```

Then users can simply:
```bash
pip install marlos
```

---

**MarlOS - Making distributed computing as easy as `pip install marlos` 🚀**
