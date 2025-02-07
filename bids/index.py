# See https://github.com/ajitesh123/codesearch/tree/main/codesearch

import shutil
from pathlib import Path

import tantivy


class BIDSIndexer:

    DISK_LOCATION_DEFAULT = Path("~").expanduser() / ".cache" / "bids"

    INDEX_SIZE = 30000000

    def __init__(self, index_path=None, debug=False):
        if index_path is None:
            self.index_path = self.DISK_LOCATION_DEFAULT / "bids_index"
        else:
            self.index_path = index_path
        self.schema = self.create_schema()
        self.index = self.initialise_index()
        self.debug = debug

    def docid(self, file_path):
        return abs(hash(file_path))

    def create_schema(self):
        schema_builder = tantivy.SchemaBuilder()
        schema_builder.add_text_field("file_path", stored=True)
        schema_builder.add_text_field("content", stored=True)
        # schema_builder.add_text_field("metadata", stored=True)
        schema_builder.add_integer_field("doc_id", stored=True, indexed=True, fast=True)

        return schema_builder.build()

    def initialise_index(self):
        Path(str(self.index_path)).mkdir(parents=True, exist_ok=True)
        return tantivy.Index(self.schema, path=str(self.index_path))

    def get_files(self, directory):
        files = []
        if self.debug:
            print(f"Find files in {directory}")
        for file_path in Path(directory).glob("**/*"):
            if self.debug:
                print(f"Processing {file_path}")
            # Ignore symlinks
            if Path(file_path).is_symlink():
                if self.debug:
                    print("Symlink ignored")
                continue
            # Ignore directories
            if Path(file_path).is_dir():
                if self.debug:
                    print("Directory ignored)")
                continue
            if not str(file_path).endswith(".json"):
                if self.debug:
                    print("Not a JSON file")
                continue
            with open(file_path, encoding="utf-8") as f:
                files.append(
                    {
                        "file_path": str(file_path),
                        "content": f.read(),
                    }
                )
        return files

    def index_files(self, directory, batch_size=1000):
        files = self.get_files(directory)
        try:
            writer = self.index.writer(self.INDEX_SIZE, 1)

            batch_count = 0
            for file_info in files:
                if self.debug:
                    print(f"Process: {file_info['file_path']}")
                doc = tantivy.Document(
                    file_path=file_info["file_path"],
                    content=file_info["content"],
                    doc_id=self.docid(file_info["file_path"]),
                )
                writer.add_document(doc)
                batch_count += 1
                if batch_count >= batch_size:
                    writer.commit()
                    batch_count = 0
            if batch_count > 0:
                writer.commit()
        except Exception as e:
            raise Exception(f"Failed to index files: {str(e)}")

    def search(self, query, limit=10):
        self.index.reload()
        parsed_query = self.index.parse_query(query, ["content"])
        searcher = self.index.searcher()

        results = []
        for score, doc_address in searcher.search(parsed_query, limit=limit).hits:
            doc = searcher.doc(doc_address)
            element = {
                "file_path": doc["file_path"][0],
                "score": score,
                "content": doc["content"][0],
            }
            if element not in results:
                results.append(element)
        return results

    def reinitialise_index(self):
        shutil.rmtree(self.index_path)
        self.create_schema()
        self.initialise_index()

    def import_data(self, filename):
        # Extract data into index
        if self.debug:
            print(f"Import file {filename}")
        # Check file exists
        if Path(filename).exists():
            # Remove existing data
            self.reinitialise_index()
            shutil.unpack_archive(filename, self.index_path, "zip")
            return True
        return False

    def export_data(self, export_filename):
        # store data in index
        shutil.make_archive(export_filename, "zip", self.index_path)

    def get_index_path(self):
        return self.index_path
