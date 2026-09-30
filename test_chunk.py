from src.common import get_collection
coll = get_collection()
results = coll.query(
    query_texts=['exit load'],
    n_results=5,
    include=['documents', 'metadatas', 'distances'],
    where={"$and": [{"scheme_name": "HDFC Balanced Advantage Fund - Direct Growth"}, {"heading": "Exit Load"}]}
)
print('IDs:', results['ids'])
for i, (doc, meta, dist) in enumerate(zip(results['documents'][0], results['metadatas'][0], results['distances'][0])):
    print('Chunk', i, 'scheme=', meta.get('scheme_name'), 'heading=', meta.get('heading'))
    print(doc[:200])
    print('---')