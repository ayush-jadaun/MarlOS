"""
Docker Job Runner
Executes jobs in Docker containers for isolation
"""
import asyncio
import docker
import tempfile
import os
from typing import Dict


class DockerRunner:
    """
    Executes jobs in Docker containers
    """
    
    def __init__(self):
        try:
            self.client = docker.from_env()
            self.available = True
            print("[DOCKER] Docker client initialized")
        except Exception as e:
            print(f"[DOCKER] Docker not available: {e}")
            self.available = False
            self.client = None
    
    async def run(self, job: dict) -> Dict:
        """
        Execute job in Docker container
        
        Job payload:
        {
            'image': 'ubuntu:22.04',
            'command': 'echo "hello"',
            'volumes': {},
            'environment': {},
            'memory_limit': '512m',
            'cpu_limit': 1.0
        }
        """
        if not self.available:
            raise Exception("Docker not available")
        
        payload = job.get('payload', {})
        image = payload.get('image', 'ubuntu:22.04')
        command = payload.get('command')
        volumes = payload.get('volumes', {})
        environment = payload.get('environment', {})
        memory_limit = payload.get('memory_limit', '512m')
        cpu_limit = payload.get('cpu_limit', 1.0)
        
        if not command:
            raise ValueError("No command specified")
        
        print(f"[DOCKER] Running in {image}: {command}")
        
        try:
            # Pull image if needed
            await self._ensure_image(image)
            
            # Run container
            container = await asyncio.to_thread(
                self.client.containers.run,
                image=image,
                command=command,
                volumes=volumes,
                environment=environment,
                mem_limit=memory_limit,
                nano_cpus=int(cpu_limit * 1e9),
                detach=False,
                remove=True,
                stdout=True,
                stderr=True
            )
            
            # Decode output
            output = container.decode('utf-8', errors='replace')
            
            return {
                'output': output,
                'success': True
            }
        
        except docker.errors.ContainerError as e:
            return {
                'output': e.stderr.decode('utf-8', errors='replace'),
                'exit_code': e.exit_status,
                'success': False,
                'error': str(e)
            }
        
        except Exception as e:
            raise Exception(f"Docker execution error: {e}")
    
    async def _ensure_image(self, image: str):
        """Pull image if not exists"""
        try:
            await asyncio.to_thread(self.client.images.get, image)
        except docker.errors.ImageNotFound:
            print(f"[DOCKER] Pulling image: {image}")
            await asyncio.to_thread(self.client.images.pull, image)


class DockerBuildRunner:
    """
    Builds Docker images from Dockerfile
    """
    
    def __init__(self):
        try:
            self.client = docker.from_env()
            self.available = True
        except Exception as e:
            print(f"[DOCKER] Docker not available: {e}")
            self.available = False
            self.client = None
    
    async def run(self, job: dict) -> Dict:
        """
        Build Docker image
        
        Job payload:
        {
            'dockerfile': 'FROM ubuntu...',
            'tag': 'myapp:latest',
            'buildargs': {}
        }
        """
        if not self.available:
            raise Exception("Docker not available")
        
        payload = job.get('payload', {})
        dockerfile_content = payload.get('dockerfile')
        tag = payload.get('tag', f"marlos-build-{job['job_id']}")
        buildargs = payload.get('buildargs', {})
        
        if not dockerfile_content:
            raise ValueError("No Dockerfile provided")
        
        print(f"[DOCKER] Building image: {tag}")
        
        try:
            # Create temp directory with Dockerfile
            with tempfile.TemporaryDirectory() as tmpdir:
                dockerfile_path = os.path.join(tmpdir, 'Dockerfile')
                with open(dockerfile_path, 'w') as f:
                    f.write(dockerfile_content)
                
                # Build image
                image, build_logs = await asyncio.to_thread(
                    self.client.images.build,
                    path=tmpdir,
                    tag=tag,
                    buildargs=buildargs,
                    rm=True
                )
                
                # Collect logs
                logs = []
                for chunk in build_logs:
                    if 'stream' in chunk:
                        logs.append(chunk['stream'])
                
                return {
                    'image_id': image.id,
                    'tag': tag,
                    'logs': ''.join(logs),
                    'success': True
                }
        
        except docker.errors.BuildError as e:
            return {
                'error': str(e),
                'logs': e.build_log,
                'success': False
            }
        
        except Exception as e:
            raise Exception(f"Docker build error: {e}")