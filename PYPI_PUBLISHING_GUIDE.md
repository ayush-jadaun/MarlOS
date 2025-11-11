# PyPI Publishing Guide for MarlOS

Complete guide to publish MarlOS on PyPI so users can install with `pip install marlos`.

---

## ✅ Pre-Publishing Checklist

Your package is **ready for PyPI**! Here's what we have:

- ✅ `pyproject.toml` - Modern Python packaging configuration
- ✅ `setup.py` - Backward compatibility (optional, can remove)
- ✅ `MANIFEST.in` - Package data specification
- ✅ `LICENSE` - MIT License
- ✅ `README.md` - Comprehensive documentation
- ✅ `cli/main.py` - CLI entry point with `marl` command
- ✅ `.gitignore` - Updated with PyPI exclusions
- ✅ Clean project structure

---

## 📦 Step 1: Create PyPI Accounts

### 1.1 Create PyPI Account (Production)

1. Go to https://pypi.org/account/register/
2. Fill in:
   - Username: `yourusername`
   - Email: Your email
   - Password: Strong password
3. Verify email

### 1.2 Create TestPyPI Account (Testing)

1. Go to https://test.pypi.org/account/register/
2. Create separate account (recommended for testing)

### 1.3 Generate API Tokens

**For PyPI (Production):**
1. Go to https://pypi.org/manage/account/
2. Scroll to "API tokens"
3. Click "Add API token"
4. Name: `marlos-upload`
5. Scope: "Entire account" (or specific to marlos project after first upload)
6. Copy the token (starts with `pypi-...`)

**For TestPyPI (Testing):**
1. Go to https://test.pypi.org/manage/account/
2. Follow same steps
3. Copy the token

---

## 🔑 Step 2: Configure Credentials

### 2.1 Create ~/.pypirc

**Linux/Mac:**
```bash
nano ~/.pypirc
```

**Windows:**
```bash
notepad %USERPROFILE%\.pypirc
```

**Content:**
```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-YOUR-PRODUCTION-TOKEN-HERE

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-YOUR-TESTPYPI-TOKEN-HERE
```

**Set permissions (Linux/Mac):**
```bash
chmod 600 ~/.pypirc
```

---

## 🛠️ Step 3: Install Build Tools

```bash
pip install --upgrade pip
pip install --upgrade build twine
```

**What these do:**
- `build` - Creates distribution packages (wheel & sdist)
- `twine` - Securely uploads packages to PyPI

---

## 🧪 Step 4: Test Build Locally

### 4.1 Clean Previous Builds

```bash
rm -rf dist/ build/ *.egg-info
```

### 4.2 Build the Package

```bash
python -m build
```

This creates:
```
dist/
├── marlos-1.0.4-py3-none-any.whl    # Wheel (binary)
└── marlos-1.0.4.tar.gz               # Source distribution
```

### 4.3 Verify Package Contents

```bash
tar -tzf dist/marlos-1.0.4.tar.gz | head -20
```

Should include:
- `agent/`
- `cli/`
- `docs/`
- `scripts/`
- `README.md`
- `LICENSE`
- etc.

---

## 🧪 Step 5: Test Upload to TestPyPI

### 5.1 Upload to TestPyPI

```bash
twine upload --repository testpypi dist/*
```

You'll see:
```
Uploading distributions to https://test.pypi.org/legacy/
Uploading marlos-1.0.4-py3-none-any.whl
100% ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Uploading marlos-1.0.4.tar.gz
100% ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

View at:
https://test.pypi.org/project/marlos/1.0.4/
```

### 5.2 Test Installation from TestPyPI

```bash
# Create test environment
python -m venv test-env
source test-env/bin/activate  # Windows: test-env\Scripts\activate

# Install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ marlos
```

**Note:** `--extra-index-url https://pypi.org/simple/` is needed because dependencies are on regular PyPI.

### 5.3 Test the CLI

```bash
marl --version
marl --help
marl  # Interactive menu
```

### 5.4 Clean Up Test

```bash
deactivate
rm -rf test-env
```

---

## 🚀 Step 6: Upload to Production PyPI

### 6.1 Final Check

- ✅ Version number is correct in `pyproject.toml`
- ✅ README.md is up to date
- ✅ All tests pass
- ✅ No sensitive data in package
- ✅ LICENSE is included

### 6.2 Upload to PyPI

```bash
twine upload dist/*
```

You'll see:
```
Uploading distributions to https://upload.pypi.org/legacy/
Uploading marlos-1.0.4-py3-none-any.whl
100% ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Uploading marlos-1.0.4.tar.gz
100% ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

View at:
https://pypi.org/project/marlos/1.0.4/
```

### 6.3 Verify on PyPI

Visit: https://pypi.org/project/marlos/

You should see:
- Package name: **marlos**
- Version: **1.0.4**
- Your README rendered
- Installation instructions
- Project links

---

## 🎉 Step 7: Test Public Installation

```bash
# Anyone can now install with:
pip install marlos

# Test it
marl --version
marl
```

**Success!** Your package is live on PyPI! 🚀

---

## 📝 Step 8: Update README

Update installation instructions in `README.md`:

```markdown
### Install with pip

```bash
pip install marlos
```

Then run:
```bash
marl  # Interactive menu
```
```

---

## 🔄 Publishing Updates

### For Version 1.0.1, 1.1.0, etc.

1. **Update version** in `pyproject.toml`:
   ```toml
   version = "1.0.1"
   ```

2. **Clean and rebuild**:
   ```bash
   rm -rf dist/ build/ *.egg-info
   python -m build
   ```

3. **Test on TestPyPI** (optional):
   ```bash
   twine upload --repository testpypi dist/*
   ```

4. **Upload to PyPI**:
   ```bash
   twine upload dist/*
   ```

5. **Tag release in Git**:
   ```bash
   git tag -a v1.0.1 -m "Release version 1.0.1"
   git push origin v1.0.1
   ```

---

## 🐛 Troubleshooting

### "File already exists on PyPI"

You can't re-upload the same version. Bump version number:
```toml
version = "1.0.1"  # Increment
```

### "Invalid or non-existent authentication information"

Check your `~/.pypirc` file:
- Token starts with `pypi-`
- No extra spaces
- File permissions: `chmod 600 ~/.pypirc`

### "Package name already taken"

Someone else has `marlos`. Try:
- `marlos-distributed`
- `marlos-os`
- `marlos-rl`

Or contact PyPI support to claim if it's abandoned.

### "README rendering issues"

Test locally:
```bash
twine check dist/*
```

### "Missing dependencies"

Ensure all dependencies are in `pyproject.toml`:
```toml
dependencies = [
  "click>=8.0.0",
  "rich>=13.0.0",
  # ... all deps
]
```

---

## 📊 Package Statistics

After publishing, you can see:
- **Downloads**: https://pypistats.org/packages/marlos
- **GitHub Stars**: Track in your repo
- **Issues**: Monitor PyPI project page

---

## 🎯 Marketing Your Package

### 1. Update GitHub README

Add PyPI badge:
```markdown
[![PyPI version](https://badge.fury.io/py/marlos.svg)](https://badge.fury.io/py/marlos)
[![Downloads](https://pepy.tech/badge/marlos)](https://pepy.tech/project/marlos)
```

### 2. Share on Social Media

**Twitter/X:**
```
🚀 MarlOS is now on PyPI!

Install with:
pip install marlos

Autonomous distributed computing with RL-based scheduling.

#Python #PyPI #DistributedSystems #MachineLearning

https://pypi.org/project/marlos/
```

**Reddit r/Python:**
```
[Project] MarlOS - Now available on PyPI

pip install marlos

Autonomous distributed OS with RL-based job scheduling.
```

### 3. Submit to Awesome Lists

- awesome-python
- awesome-distributed-systems
- awesome-reinforcement-learning

---

## 📦 Package Maintenance

### Weekly

- Monitor PyPI download stats
- Check for new issues
- Review pull requests

### Monthly

- Update dependencies
- Fix bugs
- Release new version

### Quarterly

- Major feature releases
- Documentation updates
- Performance improvements

---

## 🔒 Security Best Practices

1. **Never commit .pypirc to git** ✅ (already in .gitignore)
2. **Use API tokens, not passwords**
3. **Enable 2FA on PyPI account**
4. **Rotate tokens periodically**
5. **Monitor package for unauthorized changes**
6. **Sign releases with GPG** (optional):
   ```bash
   gpg --detach-sign -a dist/marlos-1.0.4.tar.gz
   ```

---

## 📚 Additional Resources

- **PyPI Guide**: https://packaging.python.org/tutorials/packaging-projects/
- **Twine Docs**: https://twine.readthedocs.io/
- **PEP 621**: https://peps.python.org/pep-0621/ (pyproject.toml spec)
- **Python Packaging**: https://packaging.python.org/

---

## ✅ Quick Command Reference

```bash
# Build package
python -m build

# Check package
twine check dist/*

# Upload to TestPyPI
twine upload --repository testpypi dist/*

# Upload to PyPI
twine upload dist/*

# Install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ marlos

# Install from PyPI
pip install marlos

# Update package
# 1. Bump version in pyproject.toml
# 2. rm -rf dist/ build/ *.egg-info
# 3. python -m build
# 4. twine upload dist/*
```

---

## 🎉 Success Checklist

After publishing, verify:

- [ ] Package appears on https://pypi.org/project/marlos/
- [ ] `pip install marlos` works
- [ ] `marl` command is available globally
- [ ] README renders correctly on PyPI
- [ ] All project links work
- [ ] Dependencies install correctly
- [ ] CLI is functional
- [ ] GitHub README updated with PyPI badge
- [ ] Social media announcements made
- [ ] Version tagged in git

---

**Congratulations! MarlOS is now published on PyPI!** 🎉

Users worldwide can now install it with a single command:
```bash
pip install marlos
```
