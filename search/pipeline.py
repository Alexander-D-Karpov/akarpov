from haystack import Document
from milvus_haystack import MilvusDocumentStore

ds = MilvusDocumentStore()
ds.write_documents([Document("Some Content")])
ds.get_all_documents()
