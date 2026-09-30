from src.common import get_collection
coll = get_collection()
results = coll.query(
    query_texts=['What is the exit load?'],
    n_results=5,
    include=['documents', 'metadatas', 'distances'],
    where={"scheme_name": "HDFC Balanced Advantage Fund - Direct Growth"}
)
print('IDs:', results['ids'])
for i, (doc, meta, dist) in enumerate(zip(results['documents'][0], results['metadatas'][0], results['distances'][0])):
    sim = 1.0 - dist
    print('Chunk', i, 'scheme=', meta.get('scheme_name'), 'heading=', meta.get('heading'), 'dist=', dist, 'sim=', sim)
    print(doc[:200])
    print('---')