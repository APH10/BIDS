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
  print (f"Title: {title}")
  content = json.dumps(data)
  #content = data["metadata"]["binary"]["filename"]
  print (f"Content: {content}")

  writer = index.writer()
  writer.add_document(tantivy.Document(
   doc_id=doc_id,
   title=[title],
   content=[f"""{content}"""]))
  # ... and committing
  writer.commit()
  writer.wait_merging_threads()

# Reload the index to ensure it points to the last commit.
index.reload()
searcher = index.searcher()

query = index.parse_query("sprintf", ["title", "content"])
print (f"Query search: {searcher.search(query, 3)}")
query_result = searcher.search(query, 3)
if query_result.count > 0:
    for c in range(query_result.count):
        (best_score, best_doc_address) = searcher.search(query, 3).hits[c]
        print (f"Score: {best_score}")
        print (f"Doc {best_doc_address}")
        best_doc = searcher.doc(best_doc_address)
        print (best_doc)
        hit_text = best_doc["content"][0]
        print(f"{hit_text=}")
else:
    print ("No data found")
# assert best_doc["title"] == ["The Old Man and the Sea"]

#
#
# # Snippet
# hit_text = best_doc["body"][0]
# print(f"{hit_text=}")
# assert hit_text == (
# "He was an old man who fished alone in a skiff in the "
# "Gulf Stream and he had gone eighty-four days now "
# "without taking a fish."
# )
#
# from tantivy import SnippetGenerator
# snippet_generator = SnippetGenerator.create(
#  searcher, query, schema, "body"
# )
# snippet = snippet_generator.snippet_from_doc(best_doc)
#
# highlights = snippet.highlighted()
# first_highlight = highlights[0]
# assert first_highlight.start == 93
# assert first_highlight.end == 97
# assert hit_text[first_highlight.start:first_highlight.end] == "days"
#
# html_snippet = snippet.to_html()
# assert html_snippet == (
#  "He was an old man who fished alone in a skiff in the "
#  "Gulf Stream and he had gone eighty-four <b>days</b> now "
#  "without taking a <b>fish</b>"
# )
