# Quick Install Guide for Friends

Hey! So you want to install MarlOS on your computer. Here's the easiest way:

---

## 🚀 Super Easy Installation (Windows)

### Step 1: Install Python with PATH

1. **Download Python**: Go to https://www.python.org/downloads/
2. **Run the installer**
3. **✅ IMPORTANT**: Check the box **"Add Python to PATH"** at the bottom!
   ```
   [✓] Add Python to PATH  <--- CHECK THIS BOX!
   ```
4. Click **"Install Now"**
5. Wait for installation to complete
6. Click **"Close"**

### Step 2: Install MarlOS

Open **PowerShell** or **Command Prompt** and run:

```powershell
pip install git+https://github.com/ayush-jadaun/MarlOS.git
```

Wait for it to finish...

### Step 3: Test It

```powershell
marl --help
```

If you see the MarlOS help menu, **you're done!** 🎉

---

## ⚠️ If "marl: command not found" Error

This means Python's Scripts folder isn't in your PATH. Here's how to fix it:

### Quick Fix (Windows)

1. Press `Windows + R`
2. Type `sysdm.cpl` and press Enter
3. Click **"Advanced"** tab
4. Click **"Environment Variables"**
5. Under **"User variables"**, find **"Path"** and click **"Edit"**
6. Click **"New"**
7. Add this (adjust if your Python is elsewhere):
   ```
   C:\Users\YourName\AppData\Local\Programs\Python\Python311\Scripts
   ```
   To find your exact path, run in PowerShell:
   ```powershell
   python -c "import sys; print(sys.prefix + '\\Scripts')"
   ```
8. Click **"OK"** on all windows
9. **Close and reopen PowerShell**
10. Try again: `marl --help`

---

## Alternative: No PATH Setup Needed

If you don't want to mess with PATH, you can always run:

```powershell
python -m cli.main --help
python -m cli.main status
python -m cli.main execute "echo Hello"
```

---

## 🍎 macOS / 🐧 Linux Users

### macOS

```bash
# Install
pip3 install git+https://github.com/ayush-jadaun/MarlOS.git

# If "marl: command not found", add to PATH:
echo 'export PATH="$HOME/Library/Python/3.11/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# Test
marl --help
```

### Linux

```bash
# Install
pip install --user git+https://github.com/ayush-jadaun/MarlOS.git

# If "marl: command not found", add to PATH:
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Test
marl --help
```

---

## 💡 Pro Tip: Use pipx (Recommended)

pipx automatically handles PATH for you! No manual setup needed:

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

## 📝 Quick Start After Installation

```bash
# Interactive menu
marl

# Start MarlOS
marl start

# Run a command
marl execute "echo Hello MarlOS"

# Check status
marl status

# Get help
marl --help
```

---

## ❓ Still Having Issues?

1. **Check Python version**: `python --version` (need 3.11+)
2. **Check if installed**: `pip show marlos`
3. **Find the script**: `where marl` (Windows) or `which marl` (Mac/Linux)
4. **Read the full guide**: [PATH Setup Guide](https://github.com/ayush-jadaun/MarlOS/blob/main/docs/PATH_SETUP_QUICK_REFERENCE.md)

---

## Why Does It Work on Your Friend's Laptop But Not Yours?

Your friend checked **"Add Python to PATH"** when installing Python, so the Scripts folder is already in their PATH. You probably didn't check that box (it's unchecked by default on Windows).

**Solution**: Either add to PATH manually (see above) or reinstall Python with that checkbox checked.

---

**Need more help?** Check out the full docs at https://github.com/ayush-jadaun/MarlOS
