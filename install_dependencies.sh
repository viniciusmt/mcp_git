#!/bin/bash
# Custom dependency installation script for MCP Git API

echo "Upgrading pip..."
pip install --upgrade pip

echo "Installing base dependencies..."
pip install urllib3>=2.0.0,<3.0.0
pip install charset-normalizer>=3.0.0,<4.0.0
pip install certifi>=2024.0.0

echo "Installing core dependencies..."
pip install requests>=2.31.0
pip install python-dotenv>=1.0.0

echo "Installing FastAPI ecosystem..."
pip install pydantic>=2.5.0,<3.0.0
pip install starlette>=0.35.0,<0.36.0
pip install fastapi>=0.100.0,<0.112.0
pip install uvicorn[standard]>=0.20.0

echo "Installing production server..."
pip install gunicorn>=21.0.0

echo "Installing MCP SDK (final step)..."
pip install git+https://github.com/modelcontextprotocol/python-sdk.git@main

echo "Installation complete!"
