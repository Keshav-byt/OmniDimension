#!/bin/bash

# Exit on error
set -e

echo "Installing frontend dependencies..."
cd frontend
npm install

echo "Building React frontend..."
npm run build

echo "Copying build to backend root..."
cd ..
rm -rf build
cp -r frontend/build ./build

echo "Installing backend dependencies..."
pip install -r requirements.txt
