"""
Shell Command Runner
Executes shell commands in subprocess with security controls
"""
import asyncio
import subprocess
import shlex
import os
from typing import Dict, Set


class ShellRunner:
    """
    Executes shell commands safely with whitelisting and sandboxing
    """

    # Whitelist of allowed commands (security hardening)
    ALLOWED_COMMANDS: Set[str] = {
        'ls', 'cat', 'grep', 'find', 'wc', 'head', 'tail', 'sort', 'uniq',
        'echo', 'pwd', 'whoami', 'date', 'hostname', 'uname', 'df', 'du',
        'ps', 'top', 'free', 'uptime', 'ping', 'curl', 'wget', 'git',
        'python3', 'python', 'node', 'npm', 'pip', 'docker', 'sleep'
    }

    # Blacklisted dangerous commands
    BLACKLISTED_COMMANDS: Set[str] = {
        'rm', 'rmdir', 'mkfs', 'dd', 'fdisk', 'shutdown', 'reboot', 'halt',
        'kill', 'killall', 'pkill', 'chmod', 'chown', 'chgrp', 'passwd',
        'su', 'sudo', 'systemctl', 'service', 'init'
    }

    def __init__(self, sandbox: bool = True, whitelist_enabled: bool = True):
        self.sandbox = sandbox
        self.whitelist_enabled = whitelist_enabled

    def _validate_command(self, command: str) -> None:
        """
        Validate command against whitelist/blacklist
        Raises ValueError if command is not allowed
        """
        if not command or not command.strip():
            raise ValueError("Empty command not allowed")

        # Parse command to get base executable
        try:
            parts = shlex.split(command)
        except ValueError as e:
            raise ValueError(f"Invalid command syntax: {e}")

        if not parts:
            raise ValueError("Empty command not allowed")

        # Get base command (first part or after path)
        base_command = os.path.basename(parts[0])

        # Check blacklist first (highest priority)
        if base_command in self.BLACKLISTED_COMMANDS:
            raise ValueError(f"Command '{base_command}' is blacklisted for security")

        # Check whitelist if enabled
        if self.whitelist_enabled and base_command not in self.ALLOWED_COMMANDS:
            raise ValueError(
                f"Command '{base_command}' not in whitelist. "
                f"Allowed commands: {', '.join(sorted(self.ALLOWED_COMMANDS))}"
            )

        # Check for shell injection patterns
        dangerous_patterns = [';', '&&', '||', '|', '`', '$', '>', '<', '&']
        for pattern in dangerous_patterns:
            if pattern in command and self.sandbox:
                raise ValueError(
                    f"Command contains potentially dangerous pattern '{pattern}'. "
                    "Disable sandbox mode to allow."
                )

    async def run(self, job: dict) -> Dict:
        """
        Execute shell command safely

        Job payload should contain:
        {
            'command': 'ls -la',
            'cwd': '/tmp',  # optional
            'env': {},      # optional
            'timeout': 60,  # optional
            'allow_unsafe': False  # optional, bypasses whitelist (USE WITH CAUTION)
        }
        """
        payload = job.get('payload', {})
        command = payload.get('command')
        cwd = payload.get('cwd', None)
        env = payload.get('env', None)
        timeout = payload.get('timeout', 60)
        allow_unsafe = payload.get('allow_unsafe', False)

        if not command:
            raise ValueError("No command specified")

        # Temporarily disable whitelist if explicitly allowed (and sandbox is off)
        original_whitelist = self.whitelist_enabled
        if allow_unsafe and not self.sandbox:
            self.whitelist_enabled = False
            print(f"[SHELL] ⚠️  UNSAFE MODE: Whitelist disabled for command")

        try:
            # Validate command for security FIRST
            self._validate_command(command)
        except ValueError as e:
            # Re-raise validation errors immediately
            raise e
        
        try:
            print(f"[SHELL] Executing: {command}")

            # Parse command safely using shlex
            cmd_parts = shlex.split(command)

            # Use create_subprocess_exec (NOT shell) to prevent injection
            process = await asyncio.create_subprocess_exec(
                *cmd_parts,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
                env=env
            )

            # Wait with timeout
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )

            return {
                'stdout': stdout.decode('utf-8', errors='replace'),
                'stderr': stderr.decode('utf-8', errors='replace'),
                'returncode': process.returncode,
                'success': process.returncode == 0
            }

        except asyncio.TimeoutError:
            process.kill()
            await process.wait()  # Ensure process is cleaned up
            raise Exception(f"Command timeout after {timeout}s")

        except Exception as e:
            raise Exception(f"Shell execution error: {e}")

        finally:
            # Restore whitelist setting
            self.whitelist_enabled = original_whitelist