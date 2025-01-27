# See https://github.com/ajitesh123/codesearch/tree/main/codesearch

import os
from pathlib import Path
from typing import List, Dict
import argparse
from indexer import TantivyIndexer


def get_source_files(directory: str, extensions: List[str]) -> List[Dict]:
    """Get all source files with specified extensions from a directory."""
    files = []
    for ext in extensions:
        for file_path in Path(directory).rglob(f"*.{ext}"):
            if not any(part.startswith('.') for part in file_path.parts):  # Skip hidden directories
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        files.append({
                            "file_path": str(file_path),
                            "content": content,
                            "metadata": {
                                "extension": ext,
                                "size": os.path.getsize(file_path)
                            }
                        })
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")
    return files


def main():
    parser = argparse.ArgumentParser(description='Code Search Tool')
    parser.add_argument('--index', type=str, help='Directory to index')
    parser.add_argument('--search', type=str, help='Search query')
    parser.add_argument('--extensions', type=str, default='py,js,ts,java,cpp,h,hpp',
                       help='Comma-separated list of file extensions to index')
    args = parser.parse_args()

    # Initialize indexer
    indexer = TantivyIndexer("code_search_index")

    if args.index:
        # Index the specified directory
        print(f"Indexing files in {args.index}...")
        extensions = args.extensions.split(',')
        files = get_source_files(args.index, extensions)
        print(f"Found {len(files)} files to index")
        
        indexer.batch_index_files(files)
        print("Indexing complete!")

    if args.search:
        # Search the index
        print(f"\nSearching for: {args.search}")
        results = indexer.search(args.search, limit=10)
        
        if not results:
            print("No results found.")
        else:
            print("\nSearch Results:")
            print("-" * 80)
            for i, result in enumerate(results, 1):
                print(f"{i}. {result['file_path']} (Score: {result['score']:.2f})")
                try:
                    with open(result['file_path'], 'r', encoding='utf-8') as f:
                        content = f.read()
                        preview = ' '.join(content.split()[:50]) + "..."
                        print(f"   Preview: {preview}\n")
                except Exception as e:
                    print(f"   Error reading file: {e}\n")


if __name__ == "__main__":
    main() 