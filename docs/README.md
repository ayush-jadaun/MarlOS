# MarlOS Documentation Index

Complete guide to MarlOS documentation.

## 📚 Getting Started

### Installation & Setup
- **[pip Installation](PIP_INSTALL.md)** - Install with pip and use `marl` command
  - Quickest method for most users
  - Includes PATH setup guide

- **[Install for Friends](../INSTALL_FOR_FRIENDS.md)** - Simple installation guide to share
  - Non-technical user friendly
  - Step-by-step with screenshots

- **[Interactive Installer](INSTALL.md)** - Full system setup with guided wizard
  - Automated dependency installation
  - Network configuration

- **[Quick Start Guide](QUICKSTART.md)** - 5-minute manual setup
  - For experienced users
  - Minimal configuration

- **[PATH Setup Reference](PATH_SETUP_QUICK_REFERENCE.md)** - Fix "command not found" errors
  - OS-specific instructions
  - Windows, macOS, Linux

### Using MarlOS
- **[Command Reference](COMMANDS.md)** - Complete `marl` CLI guide
  - All available commands
  - Usage examples
  - Tips & tricks

---

## 🌐 Network & Deployment

### Network Configuration
- **[User Guide: Network Modes](USER_GUIDE_NETWORK_MODES.md)** - Choose between Private and Public modes
  - Private Mode: Connect your own devices
  - Public Mode: Join global network

- **[Network Design](NETWORK_DESIGN.md)** - P2P communication architecture
  - ZeroMQ protocol
  - Peer discovery
  - Security

- **[Cross-Internet Discovery](CROSS_INTERNET_DISCOVERY.md)** - Connect devices across different networks
  - NAT traversal
  - Bootstrap servers
  - DHT integration

### Deployment
- **[Distributed Deployment](DISTRIBUTED_DEPLOYMENT.md)** - Deploy on real devices
  - Multi-device setup
  - Network configuration
  - Firewall rules

- **[Deployment Verification](DEPLOYMENT_VERIFICATION.md)** - Test your setup
  - Automated test suite
  - Connection validation
  - Performance benchmarks

- **[Share Guide](SHARE.md)** - Share MarlOS with your team
  - Quick sharing links
  - Team deployment
  - Collaboration tips

---

## ⚙️ Configuration Management

### Configuration System
- **[Configuration Architecture](CONFIG_ARCHITECTURE.md)** - Two-tier config system design
  - System defaults vs node configs
  - Configuration precedence
  - Architecture decisions

- **[Configuration Management Guide](CONFIG_MANAGEMENT_GUIDE.md)** - Manage node configurations
  - Create, edit, delete nodes
  - Configuration operations
  - Best practices

- **[Full Configuration Usage](FULL_CONFIG_USAGE.md)** - Complete config reference
  - All configuration options
  - Environment variables
  - YAML configuration
  - Per-node settings

- **[Predictive Config](PREDICTIVE_CONFIG.md)** - Predictive pre-execution settings
  - Enable/disable prediction
  - Economic constraints
  - RL speculation

---

## 🏗️ Architecture & Design

### Core Systems
- **[RL Architecture](ARCHITECTURE_RL.md)** - Reinforcement learning system
  - PPO agent design
  - State representation
  - Bidding policy

- **[Token Economy](ARCHITECTURE_TOKEN.md)** - Economic system design
  - MarlCredits token system
  - Fairness mechanisms
  - Progressive taxation

- **[RL Prediction Design](RL_PREDICTION_DESIGN.md)** - Predictive pre-execution
  - Pattern detection
  - Speculative execution
  - Cache system

### Reliability
- **[Checkpoint & Recovery](CHECKPOINT_RECOVERY_GUIDE.md)** - Fault tolerance
  - Job checkpointing
  - Failure recovery
  - Migration strategies

---

## 🔧 Developer Guides

### Integration
- **[Integration Guide](INTEGRATION_GUIDE.md)** - Integrate predictive system
  - Code modifications
  - Hook integration
  - Testing

### Project Structure
- **[Project Structure](../PROJECT_STRUCTURE.md)** - Codebase organization
  - Directory layout
  - File naming conventions
  - Quick navigation

### Publishing
- **[PyPI Publishing Guide](../PYPI_PUBLISHING_GUIDE.md)** - Publish to PyPI
  - Package preparation
  - PyPI account setup
  - Publishing steps

---

## 📖 Documentation by Use Case

### I want to...

#### Install MarlOS
1. Start with [pip Installation](PIP_INSTALL.md)
2. If issues, check [PATH Setup](PATH_SETUP_QUICK_REFERENCE.md)
3. Share with friends: [Install for Friends](../INSTALL_FOR_FRIENDS.md)

#### Deploy MarlOS on Multiple Devices
1. Read [Quick Start](QUICKSTART.md)
2. Follow [Distributed Deployment](DISTRIBUTED_DEPLOYMENT.md)
3. Choose network mode: [Network Modes Guide](USER_GUIDE_NETWORK_MODES.md)
4. Verify setup: [Deployment Verification](DEPLOYMENT_VERIFICATION.md)

#### Configure My Nodes
1. Understand [Configuration Architecture](CONFIG_ARCHITECTURE.md)
2. Use [Configuration Management Guide](CONFIG_MANAGEMENT_GUIDE.md)
3. Reference [Full Configuration Usage](FULL_CONFIG_USAGE.md)

#### Understand the System
1. Read [Network Design](NETWORK_DESIGN.md)
2. Learn [RL Architecture](ARCHITECTURE_RL.md)
3. Explore [Token Economy](ARCHITECTURE_TOKEN.md)

#### Customize Behavior
1. Check [Configuration Usage](FULL_CONFIG_USAGE.md)
2. Adjust [Predictive Config](PREDICTIVE_CONFIG.md)
3. Use [Integration Guide](INTEGRATION_GUIDE.md) for code changes

---

## 🆘 Troubleshooting

### Common Issues

**"marl: command not found"**
→ See [PATH Setup Reference](PATH_SETUP_QUICK_REFERENCE.md)

**Can't connect nodes across different networks**
→ Read [Cross-Internet Discovery](CROSS_INTERNET_DISCOVERY.md)

**Installation fails**
→ Check [pip Installation](PIP_INSTALL.md) troubleshooting section

**Need to configure node behavior**
→ Use [Configuration Management](CONFIG_MANAGEMENT_GUIDE.md)

---

## 📝 Documentation Standards

### For Users
- Guides are task-oriented
- Include working examples
- Step-by-step instructions
- Troubleshooting sections

### For Developers
- Architecture docs explain design decisions
- Integration guides show code modifications
- Reference docs cover all options

---

## 🔄 Keep Documentation Updated

When adding features:
1. Update relevant architecture docs
2. Add usage examples to guides
3. Update command reference if CLI changes
4. Add to this index

---

## 📞 Need Help?

- **GitHub Issues**: https://github.com/ayush-jadaun/MarlOS/issues
- **Demo Video**: https://youtu.be/EGv7Z3kXv30
- **Presentation**: https://www.canva.com/design/DAG4KrB5-D0/W-mglhEG6lW3rpzn7PW4BA/view

---

**Last Updated**: November 2025
**Version**: 1.0.5
