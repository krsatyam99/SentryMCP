from pathlib import Path
from setuptools import find_packages, setup

README = Path(__file__).with_name("README.md").read_text(encoding="utf-8")

setup(
    name="cross-industry-voice-dataguard",
    version="0.1.0",
    description="POC for a pluggable AI compliance voice auditing platform.",
    long_description=README,
    long_description_content_type="text/markdown",
    author="AgentAI Developer",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.11",
    install_requires=[
        "fastapi==0.111.1",
        "uvicorn[standard]==0.49.0",
        "boto3==1.43.23",
        "httpx==0.28.1",
        "mcp==1.27.2",
        "python-dotenv==1.0.0",
        "pydantic==2.13.4",
        "starlette==0.37.2",
    ],
    extras_require={
        "dev": [
            "pytest==8.4.2",
            "pytest-asyncio==0.24.0",
        ],
    },
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
