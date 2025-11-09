#!/bin/bash

# Verify .gitignore is working correctly

echo "🔍 Verifying .gitignore configuration..."
echo ""

# Initialize git if not already
if [ ! -d .git ]; then
    git init --quiet
    echo "✅ Git repository initialized"
fi

echo ""
echo "Testing critical paths that MUST be ignored:"
echo "=============================================="

PATHS_TO_IGNORE=(
    "node_modules"
    "frontend/node_modules"
    "frontend/build"
    "backend/__pycache__"
    "config/__pycache__"
    ".env"
    "*.pyc"
    "*.log"
    "data"
    "temp"
)

ALL_IGNORED=true

for path in "${PATHS_TO_IGNORE[@]}"; do
    if git check-ignore "$path" > /dev/null 2>&1; then
        echo "✅ $path - IGNORED"
    else
        echo "❌ $path - NOT IGNORED (WARNING!)"
        ALL_IGNORED=false
    fi
done

echo ""
echo "=============================================="

if [ "$ALL_IGNORED" = true ]; then
    echo "✅ All critical paths are properly ignored!"
    echo ""
    echo "Safe to push to GitHub! 🚀"
else
    echo "⚠️  WARNING: Some paths are not ignored!"
    echo "Please review .gitignore before pushing to GitHub"
fi

echo ""
echo "To see what would be committed, run:"
echo "  git add -n ."
echo ""
