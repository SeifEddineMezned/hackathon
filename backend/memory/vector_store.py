import faiss
import numpy as np
import pickle
import os
from threading import Lock
from typing import List, Tuple, Optional

from backend.config import VECTOR_STORE_PATH


class VectorStore:
    def __init__(self):
        self.index_path = f"{VECTOR_STORE_PATH}.index"
        self.mapping_path = f"{VECTOR_STORE_PATH}.pkl"  # int_id -> event_uuid
        self.dimension = 768  # nomic-embed-text dim
        self.lock = Lock()

        self.id_map = {}
        self.next_id = 0

        if os.path.exists(self.index_path) and os.path.exists(self.mapping_path):
            self.load()
        else:
            self.index = faiss.IndexFlatL2(self.dimension)

    def load(self):
        print("Loading vector store...")
        self.index = faiss.read_index(self.index_path)
        with open(self.mapping_path, "rb") as f:
            data = pickle.load(f)
            self.id_map = data["id_map"]
            self.next_id = data["next_id"]

    def save(self):
        with self.lock:
            faiss.write_index(self.index, self.index_path)
            with open(self.mapping_path, "wb") as f:
                pickle.dump({"id_map": self.id_map, "next_id": self.next_id}, f)

    def add_event(self, event_uuid: str, vector: List[float]) -> Optional[int]:
        if not vector or len(vector) != self.dimension:
            print(f"Vector dim mismatch or empty: {len(vector) if vector else 0}")
            return None

        vector_np = np.array([vector], dtype=np.float32)

        with self.lock:
            internal_id = self.next_id
            self.index.add(vector_np)
            self.id_map[internal_id] = event_uuid
            self.next_id += 1
            self.save()

        return internal_id

    def search(self, query_vector: List[float], top_k: int = 5) -> List[Tuple[str, float]]:
        if not query_vector:
            return []

        vector_np = np.array([query_vector], dtype=np.float32)
        distances, indices = self.index.search(vector_np, top_k)

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx != -1 and idx in self.id_map:
                # returns (event_uuid, L2_distance)
                results.append((self.id_map[idx], float(dist)))

        return results


store = VectorStore()
