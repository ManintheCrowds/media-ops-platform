"""Setup script for Pi Client."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="pi-client",
    version="1.0.0",
    author="Educational Platform",
    description="Raspberry Pi client for educational platform",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Education",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.9",
    install_requires=[
        "httpx>=0.24.0",
        "aiofiles>=23.0.0",
        "pyyaml>=6.0",
        "pydantic>=2.0.0",
        "fastapi>=0.100.0",
        "uvicorn[standard]>=0.23.0",
        "jinja2>=3.1.0",
        "websockets>=11.0",
        "cryptography>=41.0.0",
        "pyjwt>=2.8.0",
    ],
    extras_require={
        "hardware": [
            "RPi.GPIO>=0.7.1",
            "gpiozero>=1.6.2",
            "picamera2>=0.3.12",
            "pygame>=2.5.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "pi-client=pi_client.main:main",
        ],
    },
)


