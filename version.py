#!/usr/bin/env python3
"""
Version management for Zysys API Test Framework.
Handles automatic version incrementing and version history.
"""

import json
import os
from datetime import datetime
from pathlib import Path

VERSION_FILE = "version.json"

def load_version():
    """Load the current version from version.json"""
    if not Path(VERSION_FILE).exists():
        # Initialize with version 1.0.0
        version_data = {
            "major": 1,
            "minor": 0,
            "patch": 0,
            "created": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "history": [
                {
                    "version": "1.0.0",
                    "date": datetime.now().isoformat(),
                    "description": "Initial release"
                }
            ]
        }
        save_version(version_data)
        return version_data
    
    with open(VERSION_FILE, 'r') as f:
        return json.load(f)

def save_version(version_data):
    """Save version data to version.json"""
    with open(VERSION_FILE, 'w') as f:
        json.dump(version_data, f, indent=2)

def get_version_string(version_data):
    """Get version as string (e.g., '1.2.3')"""
    return f"{version_data['major']}.{version_data['minor']}.{version_data['patch']}"

def increment_version(version_type="patch"):
    """Increment version number based on type"""
    version_data = load_version()
    
    if version_type == "major":
        version_data["major"] += 1
        version_data["minor"] = 0
        version_data["patch"] = 0
    elif version_type == "minor":
        version_data["minor"] += 1
        version_data["patch"] = 0
    else:  # patch
        version_data["patch"] += 1
    
    version_data["last_updated"] = datetime.now().isoformat()
    
    # Add to history
    version_string = get_version_string(version_data)
    version_data["history"].append({
        "version": version_string,
        "date": datetime.now().isoformat(),
        "description": f"Auto-incremented {version_type} version"
    })
    
    save_version(version_data)
    return version_data

def get_current_version():
    """Get current version data"""
    return load_version()

def get_version_for_header():
    """Get version string formatted for header"""
    version_data = get_current_version()
    return get_version_string(version_data)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        version_type = sys.argv[1]
        if version_type in ["major", "minor", "patch"]:
            new_version = increment_version(version_type)
            print(f"✅ Version incremented to {get_version_string(new_version)}")
        else:
            print("❌ Invalid version type. Use: major, minor, or patch")
    else:
        # Just show current version
        version_data = get_current_version()
        print(f"Current version: {get_version_string(version_data)}")
        print(f"Version history: {len(version_data['history'])} releases")
        print("\nSemantic Versioning Guide:")
        print("  major - Breaking changes (incompatible API changes)")
        print("  minor - New features (backward compatible)")
        print("  patch - Bug fixes (backward compatible)") 