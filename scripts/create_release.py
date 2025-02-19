import os
import shutil
import subprocess
import json
from datetime import datetime
from pathlib import Path
import yaml

def get_version():
    """Get version from git tags."""
    try:
        result = subprocess.run(
            ['git', 'describe', '--tags', '--abbrev=0'],
            capture_output=True,
            text=True
        )
        return result.stdout.strip()
    except:
        return 'v1.0.0'  # Default version

def create_release_package():
    """Create release package with all necessary files."""
    # Setup paths
    release_dir = Path('release')
    if release_dir.exists():
        shutil.rmtree(release_dir)
    release_dir.mkdir()
    
    # Copy source files
    shutil.copytree('src', release_dir / 'src')
    shutil.copytree('scripts', release_dir / 'scripts')
    shutil.copytree('docs', release_dir / 'docs')
    
    # Copy configuration
    os.makedirs(release_dir / 'config')
    shutil.copy('config/config.example.yaml', release_dir / 'config')
    
    # Create version file
    version = get_version()
    version_info = {
        'version': version,
        'release_date': datetime.now().isoformat(),
        'python_version': '3.8+',
        'dependencies': {
            'pytorch': '1.9+',
            'fastapi': '0.68+',
            'streamlit': '1.0+'
        }
    }
    
    with open(release_dir / 'version.json', 'w') as f:
        json.dump(version_info, f, indent=2)
    
    # Create release archive
    shutil.make_archive(
        f'market_maker_{version}',
        'zip',
        release_dir
    )
    
    print(f"Created release package: market_maker_{version}.zip")

def run_release_checks():
    """Run pre-release checks."""
    checks = [
        ('Running unit tests...', ['pytest', 'tests/unit']),
        ('Running system tests...', ['pytest', 'tests/system']),
        ('Checking code style...', ['flake8', 'src']),
        ('Checking type hints...', ['mypy', 'src']),
        ('Checking dependencies...', ['pip', 'check']),
    ]
    
    for message, command in checks:
        print(message)
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Check failed: {' '.join(command)}")
            print(result.stdout)
            print(result.stderr)
            return False
    return True

def main():
    """Main release creation process."""
    print("Starting release creation process...")
    
    if not run_release_checks():
        print("Release checks failed. Aborting.")
        return
    
    create_release_package()
    
    print("Release creation completed successfully.")

if __name__ == "__main__":
    main() 