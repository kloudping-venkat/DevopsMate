"""
Setup script for DevopsMate Agent.
Similar to Datadog's build system.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read version
version_file = Path(__file__).parent / "agent" / "__init__.py"
version = "1.0.0"
if version_file.exists():
    for line in version_file.read_text().splitlines():
        if line.startswith("__version__"):
            version = line.split("=")[1].strip().strip('"').strip("'")
            break

# Read README
readme_file = Path(__file__).parent / "README.md"
long_description = ""
if readme_file.exists():
    long_description = readme_file.read_text()

setup(
    name="devopsmate-agent",
    version=version,
    description="DevopsMate Universal Agent - Observability and Monitoring Agent",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="DevopsMate Team",
    author_email="support@devopsmate.com",
    url="https://github.com/devopsmate/agent",
    packages=find_packages(exclude=["tests", "*.tests", "*.tests.*"]),
    python_requires=">=3.11",
    install_requires=[
        "psutil>=5.9.0",
        "docker>=6.0.0",
        "kubernetes>=27.0.0",
        "aiohttp>=3.9.0",
        "pyyaml>=6.0",
        "asyncio",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "mypy>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "devopsmate-agent=agent.cmd.agent.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: System Administrators",
        "Intended Audience :: Developers",
        "Topic :: System :: Monitoring",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
