import pathlib
import tantivy
import os
import json

# Declaring our schema.
schema_builder = tantivy.SchemaBuilder()
schema_builder.add_text_field("title", stored=True)
schema_builder.add_text_field("content", stored=True, tokenizer_name='raw')
schema_builder.add_text_field("doc_id",stored=True)
schema = schema_builder.build()

# Creating our index (on disk)
index = tantivy.Index(schema, path=os.getcwd() + '/index')

# Add documents
for bids_file in ["gnu_ar.json", "gnu_as.json"]:
  data = json.load(open(bids_file, "r", encoding="utf-8"))
  doc_id = data["metadata"]["id"]
  title = data["metadata"]["binary"]["description"]

  with open(bids_file, 'r', encoding='utf-8') as f:
    content = f.read()

  writer = index.writer()
  writer.add_document(tantivy.Document(
    doc_id=doc_id,
    title=title,
    content=content
  ))
  # ... and committing
  writer.commit()
  writer.wait_merging_threads()
