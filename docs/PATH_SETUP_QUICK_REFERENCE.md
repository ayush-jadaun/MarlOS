# PATH Setup Quick Reference

**Problem:** After running `pip install marlos`, the `marl` command doesn't work.

**Why:** pip doesn't automatically add Python's Scripts directory to your system PATH.

---

## Quick Fixes by OS

### 🪟 Windows

**Find your Scripts directory:**
```powershell
python -c "import sys; print(sys.prefix + '\\Scripts')"
```

**Add to PATH (GUI method):**
1. Press `Windows + R`, type `sysdm.cpl`, press Enter
2. Advanced → Environment Variables
3. Select "Path" → Edit → New
4. Paste the Scripts directory path
5. OK → Restart terminal

**Or use PowerShell (as Admin):**
```powershell
$scriptsPath = "C:\Users\YourName\AppData\Local\Programs\Python\Python311\Scripts"
[Environment]::SetEnvironmentVariable("Path", $env:Path + ";$scriptsPath", "User")
```

---

### 🐧 Linux

**Add to ~/.bashrc or ~/.zshrc:**
```bash
export PATH="$HOME/.local/bin:$PATH"
```

**Then reload:**
```bash
source ~/.bashrc  # or ~/.zshrc
```

**Or install system-wide:**
```bash
sudo pip install marlos
```

---

### 🍎 macOS

**Add to ~/.zshrc or ~/.bash_profile:**
```bash
export PATH="$HOME/Library/Python/3.11/bin:$PATH"
```
(Change `3.11` to your Python version)

**Then reload:**
```bash
source ~/.zshrc  # or ~/.bash_profile
```

**Or use Homebrew Python:**
```bash
brew install python3
pip3 install marlos
```

---

## Best Solution: Use pipx

pipx automatically handles PATH for CLI tools:

```bash
# Install pipx
pip install pipx
pipx ensurepath

# Close and reopen terminal

# Install marlos
pipx install git+https://github.com/ayush-jadaun/MarlOS.git

# Done!
marl --help
```

---

## Alternative: No PATH Changes Needed

Run marlos without adding to PATH:

```bash
python -m cli.main
python -m cli.main status
python -m cli.main execute "echo test"
```

---

## Verification

```bash
# Check if marl is found
which marl       # Linux/Mac
where marl       # Windows

# Test it
marl version
marl --help
```

---

**Full detailed guide:** [Complete PATH Setup Guide](./PIP_INSTALL.md#-adding-python-scripts-to-path---complete-guide)
