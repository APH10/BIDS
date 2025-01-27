import tantivy
import os
import sys

# Declaring our schema.
schema_builder = tantivy.SchemaBuilder()
schema_builder.add_text_field("title", stored=True)
schema_builder.add_text_field("content", stored=True, tokenizer_name='raw')
schema_builder.add_text_field("doc_id",stored=True)
schema = schema_builder.build()

# Creating our index (on disk)
index = tantivy.Index(schema, path=os.getcwd() + '/index')

searcher = index.searcher()

search_term = sys.argv[1]

query = index.parse_query(search_term, ["title", "content"])
#query = index.parse_query(search_term)
print (f"Query search: {searcher.search(query)}")
query_result = searcher.search(query)
if query_result.count > 0:
    for h in searcher.search(query).hits:
        (best_score, best_doc_address) = h
        print (f"Score: {best_score}")
        print (f"Doc {best_doc_address}")
        best_doc = searcher.doc(best_doc_address)
        print (best_doc)
        hit_text = best_doc["content"]
        print(f"{hit_text=}")
else:
    print ("No data found")