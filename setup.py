#!/usr/bin/env python3
"""
MarlOS - Autonomous Distributed Computing Operating System
Setup configuration for pip installation
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read long description from README
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

# Read requirements
requirements = []
with open('requirements.txt', 'r') as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name='marlos',
    version='1.0.0',
    description='Autonomous Distributed Computing Operating System with Reinforcement Learning',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Team async_await',
    author_email='ayushjadaun6@gmail.com',
    url='https://github.com/ayush-jadaun/MarlOS',
    license='MIT',

    # Package discovery
    packages=find_packages(exclude=['tests', 'docs', 'dashboard']),
    include_package_data=True,

    # Python version requirement
    python_requires='>=3.11',

    # Dependencies
    install_requires=requirements,

    # CLI entry points
    entry_points={
        'console_scripts': [
            'marl=cli.main:cli',
        ],
    },

    # Package data
    package_data={
        'agent': ['*.yml', '*.json'],
        'rl_trainer': ['models/*.zip'],
    },

    # Classifiers for PyPI
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Topic :: System :: Distributed Computing',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Operating System :: OS Independent',
        'Environment :: Console',
    ],

    # Keywords
    keywords='distributed-computing reinforcement-learning p2p autonomous-systems blockchain economics',

    # Project URLs
    project_urls={
        'Bug Reports': 'https://github.com/ayush-jadaun/MarlOS/issues',
        'Source': 'https://github.com/ayush-jadaun/MarlOS',
        'Documentation': 'https://github.com/ayush-jadaun/MarlOS/blob/main/README.md',
    },
)
