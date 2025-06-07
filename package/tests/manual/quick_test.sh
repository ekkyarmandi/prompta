#!/bin/bash

# Quick Manual Test for Prompta CLI
# Tests the most essential functionality

set -e

echo "🧪 Quick Prompta CLI Test"
echo "========================="

# Test basic commands
echo "1. Testing version..."
python -m prompta --version

echo -e "\n2. Testing status..."
python -m prompta status

echo -e "\n3. Testing ping..."
python -m prompta ping

echo -e "\n4. Testing project list..."
python -m prompta project list --page-size 3

echo -e "\n5. Testing prompt list..."
python -m prompta prompt list --page-size 3

echo -e "\n6. Testing search..."
python -m prompta prompt search react

echo -e "\n7. Testing help commands..."
python -m prompta --help > /dev/null
python -m prompta status --help > /dev/null
python -m prompta project --help > /dev/null
python -m prompta prompt --help > /dev/null
python -m prompta export --help > /dev/null

echo -e "\n✅ All basic tests passed!"
echo "🎉 CLI is working correctly!"