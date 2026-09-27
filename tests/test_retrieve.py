from src.retrieve import retrieve_chunks

chunks, scores = retrieve_chunks('What is my portfolio value?')
print(f'Chunks: {len(chunks)}')
for c, s in zip(chunks, scores):
    print(f'  Score: {s:.4f}, Chunk: {c["chunk_id"]}')