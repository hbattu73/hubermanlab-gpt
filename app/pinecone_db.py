import logging
import pinecone

from pinecone_text.hybrid import hybrid_convex_scale
from ml import zero_shot_classify
from schemas import Query
from config import settings

class PineconeDB():
    def __init__(self):
        self.api_key = settings.pinecone_api_key
        self.env = settings.pinecone_env
        self.index_name = settings.pinecone_index
        self.logger = logging.getLogger(settings.logger_name)
        self.init_db()
      
      
    def init_db(self) -> None:
        pinecone.init(
            api_key=self.api_key,
            environment=self.env
        )

        self.index = pinecone.Index(self.index_name)
        stats = self.index.describe_index_stats()
        self.logger.info("Pinecone DB Initialized...")
        self.logger.info(f"Dimension: {stats['dimension']}")
        self.logger.info(f"Index Capacity: {stats['index_fullness']}")
        self.logger.info(f"Namespaces: {list(stats['namespaces'].keys())}")
        self.logger.info(f"Total Vectors: {stats['total_vector_count']}")


    async def query_db(self, payload: Query, dense: list[float], sparse: dict[str, list]) -> list[dict]:
        try:
            index_desc = pinecone.describe_index(self.index_name)
            self.logger.info(f"Querying index: {index_desc[0]}...")
        except Exception as err:
            self.logger.warning(f"Expired connection. Re-initializing connection to Pinecone DB...")
            self.init_db()
        
        # classify query as either question or search term
        class_ = await zero_shot_classify(payload)
        vector, sparse_vector = dense, sparse
        if settings.hybrid_scale:
            # if search term, then conduct scaled sparse vector similarity search using an alpha value closer to 0
            if class_ == "search term":
                self.logger.info(f"Conducting scaled sparse vector search using alpha = {settings.sparse_alpha_value}")
                vector, sparse_vector = hybrid_convex_scale(dense, sparse, alpha=settings.sparse_alpha_value)
            # if question, then conduct scaled dense vector similarity search using an alpha value closer to 1
            else:
                self.logger.info(f"Conducting scaled dense vector search using alpha = {settings.dense_alpha_value}")
                vector, sparse_vector = hybrid_convex_scale(dense, sparse, alpha=settings.dense_alpha_value)
  
        result = self.index.query(
            top_k = settings.top_k,
            vector = vector,
            sparse_vector = sparse_vector,
            namespace=settings.pinecone_namespace,
            include_metadata=True
        )
        return result['matches']
