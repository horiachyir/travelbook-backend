#!/bin/bash

# Token Blacklist Migration Script
# This script migrates the database to support token blacklist functionality

echo "=================================="
echo "Token Blacklist Migration Script"
echo "=================================="
echo ""

# Check if we're in the backend directory
if [ ! -f "manage.py" ]; then
    echo "Error: This script must be run from the backend directory"
    echo "Please cd to the backend directory and run: ./migrate_token_blacklist.sh"
    exit 1
fi

echo "Step 1: Creating migrations for token blacklist..."
python3 manage.py makemigrations
echo ""

echo "Step 2: Running migrations..."
python3 manage.py migrate
echo ""

echo "Step 3: Verifying migration..."
python3 manage.py showmigrations token_blacklist
echo ""

echo "=================================="
echo "Migration completed successfully!"
echo "=================================="
echo ""
echo "Next steps:"
echo "1. Restart your Django server"
echo "2. Users should logout and login again to get new tokens"
echo "3. See TOKEN_REFRESH_MIGRATION.md for more details"
echo ""
