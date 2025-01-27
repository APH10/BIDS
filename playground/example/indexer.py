# See https://github.com/ajitesh123/codesearch/tree/main/codesearch

import os
from typing import List, Dict, Optional
import tantivy
from threading import Lock


class TantivyIndexer:
    def __init__(self, index_path: str):
        """Initialize the Tantivy indexer."""
        self.index_path = index_path
        self.schema = self._create_schema()
        self.index = self._initialize_index()
        self.writer_lock = Lock()
        self.writer = None
        self.MAX_WORKERS = 4

    def _create_schema(self):
        """Create the schema for the index"""
        schema_builder = tantivy.SchemaBuilder()
        schema_builder.add_text_field("file_path", stored=True)
        schema_builder.add_text_field("content", stored=True)
        schema_builder.add_text_field("metadata", stored=True)
        schema_builder.add_integer_field("doc_id", stored=True, indexed=True, fast=True)
        
        return schema_builder.build()

    def _initialize_index(self):
        """Initialize or load the existing index"""
        os.makedirs(self.index_path, exist_ok=True)
        return tantivy.Index(self.schema, path=self.index_path)

    def _get_writer(self):
        """Get a writer instance, creating it if necessary"""
        with self.writer_lock:
            if self.writer is None:
                self.writer = self.index.writer(30_000_000, 1)
            return self.writer

    def _reset_writer(self):
        """Reset the writer"""
        with self.writer_lock:
            self.writer = None

    def index_file(self, file_path: str, content: str, metadata: Optional[Dict] = None) -> None:
        """Index a single file."""
        try:
            writer = self._get_writer()
            doc_id = abs(hash(file_path))
            doc = tantivy.Document(
                file_path=file_path,
                content=content,
                metadata=str(metadata or {}),
                doc_id=doc_id
            )
            writer.add_document(doc)
            writer.commit()
        except Exception as e:
            self._reset_writer()
            raise Exception(f"Failed to index file: {str(e)}")

    def batch_index_files(self, files: List[Dict], batch_size: int = 1000) -> None:
        """Index multiple files in batches."""
        try:
            writer = self._get_writer()
            batch_count = 0
            
            for file_info in files:
                doc = tantivy.Document(
                    file_path=file_info["file_path"],
                    content=file_info["content"],
                    metadata=str(file_info.get("metadata", {})),
                    doc_id=abs(hash(file_info["file_path"]))
                )
                writer.add_document(doc)
                batch_count += 1

                if batch_count >= batch_size:
                    writer.commit()
                    batch_count = 0

            if batch_count > 0:
                writer.commit()

        except Exception as e:
            self._reset_writer()
            raise Exception(f"Failed to batch index files: {str(e)}")

    def delete_file(self, file_path: str) -> None:
        """Remove a file from the index."""
        try:
            doc_id = abs(hash(file_path))
            writer = self._get_writer()
            writer.delete_documents("doc_id", doc_id)
            writer.commit()
            self.index.reload()
        except Exception as e:
            self._reset_writer()
            raise Exception(f"Failed to delete file: {str(e)}")

    def update_file(self, file_path: str, content: str, metadata: Optional[Dict] = None) -> None:
        """Update an existing file in the index."""
        self.delete_file(file_path)
        self.index_file(file_path, content, metadata)

    def search(self, query: str, limit: int = 10) -> List[Dict[str, float]]:
        """Search the index."""
        self.index.reload()
        parsed_query = self.index.parse_query(query, ["content"])
        searcher = self.index.searcher()
        
        results = []
        for score, doc_address in searcher.search(parsed_query, limit=limit).hits:
            doc = searcher.doc(doc_address)
            results.append({
                "file_path": doc["file_path"][0],
                "score": score
            })
        return results 