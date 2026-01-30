import chromadb
from litellm import embedding
from typing import List, Dict
import hashlib

class VectorStore:
    def __init__(self):
        self.client = chromadb.PersistentClient(path="./chroma_db")
        self.collection = self.client.get_or_create_collection(
            name="insurance_docs",
            metadata={"hnsw:space": "cosine"}
        )
    
    def embed_text(self, text: str) -> List[float]:
        response = embedding(
            model="text-embedding-3-small",
            input=[text]
        )
        return response.data[0]['embedding']
    
    def add_documents(self, chunks: List[Dict[str, str]]):
        documents = []
        embeddings = []
        ids = []
        metadatas = []
        
        for chunk in chunks:
            text = chunk['text']
            doc_id = hashlib.md5(text.encode()).hexdigest()
            
            documents.append(text)
            embeddings.append(self.embed_text(text))
            ids.append(doc_id)
            metadatas.append({
                'source': chunk.get('source', 'unknown'),
                'page': str(chunk.get('page', 0))
            })
        
        self.collection.add(
            documents=documents,
            embeddings=embeddings,
            ids=ids,
            metadatas=metadatas
        )
    
    def search(self, query: str, n_results: int = 5) -> List[Dict]:
        query_embedding = self.embed_text(query)
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        
        return [
            {
                'text': doc,
                'source': meta.get('source', 'unknown'),
                'page': meta.get('page', '0'),
                'distance': dist
            }
            for doc, meta, dist in zip(
                results['documents'][0],
                results['metadatas'][0],
                results['distances'][0]
            )
        ]

vector_store = VectorStore()
