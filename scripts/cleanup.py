import shutil
from pathlib import Path
import os

def cleanup_project():
    """Clean up project structure by removing empty directories and duplicates."""
    
    # Root project directory
    project_root = Path('.')
    
    # Remove empty directories in src/
    src_dirs_to_check = [
        'src/data/capture',
        'src/data/excel',
        'src/data/storage',
        'src/models/agents',
        'src/models/evaluation',
        'src/models/training',
        'src/ui/controls',
        'src/ui/dashboard',
        'src/ui/visuals',
        'src/utils'
    ]
    
    # Remove empty test directories
    test_dirs_to_check = [
        'tests/integration',
        'tests/performance'
    ]
    
    # Remove empty directories
    for dir_path in src_dirs_to_check + test_dirs_to_check:
        path = project_root / dir_path
        if path.exists() and not any(path.iterdir()):
            print(f"Removing empty directory: {dir_path}")
            path.rmdir()
    
    # Remove old neon_market_maker directory if it exists
    neon_dir = project_root / 'neon_market_maker'
    if neon_dir.exists():
        print("Removing neon_market_maker directory")
        shutil.rmtree(neon_dir)
    
    # Remove logs directory if empty
    logs_dir = project_root / 'logs'
    if logs_dir.exists() and not any(logs_dir.iterdir()):
        print("Removing empty logs directory")
        logs_dir.rmdir()
    
    # Remove requirements-windows.txt if exists
    windows_req = project_root / 'requirements-windows.txt'
    if windows_req.exists():
        print("Removing requirements-windows.txt")
        windows_req.unlink()
    
    # Ensure we keep only one instructions.md
    old_instructions = project_root / 'neon_market_maker' / 'instructions.md'
    if old_instructions.exists():
        print("Removing duplicate instructions.md")
        old_instructions.unlink()
    
    print("Cleanup completed successfully!")

if __name__ == "__main__":
    cleanup_project() 