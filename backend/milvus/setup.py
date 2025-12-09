from backend.utils.config import COLLECTION_NAME
from pymilvus import MilvusClient, DataType, Function, FunctionType

client = MilvusClient(uri="http://localhost:19530")

schema = client.create_schema()
schema.add_field(field_name="id", datatype=DataType.VARCHAR, max_length=64, is_primary=True, auto_id=False)
schema.add_field(field_name="user_id", datatype=DataType.VARCHAR, max_length=64)
schema.add_field(field_name="type", datatype=DataType.VARCHAR, max_length=32)
schema.add_field(field_name="category", datatype=DataType.VARCHAR, max_length=32)
schema.add_field(field_name="date", datatype=DataType.VARCHAR, max_length=64)
schema.add_field(field_name="amount", datatype=DataType.FLOAT)
schema.add_field(field_name="embedding", datatype=DataType.FLOAT_VECTOR, dim=384)
schema.add_field(field_name="sparse_emb", datatype=DataType.SPARSE_FLOAT_VECTOR)
schema.add_field(field_name="text", datatype=DataType.VARCHAR, max_length=512, enable_analyzer=True)
schema.add_field(field_name="metadata", datatype=DataType.JSON)

bm25_function = Function(
    name="text_bm25_emb",
    input_field_names=["text"],
    output_field_names=["sparse_emb"],
    function_type=FunctionType.BM25,
)
schema.add_function(bm25_function)

index_params = client.prepare_index_params()
index_params.add_index(
    field_name="embedding",
    index_type="HNSW",
    metric_type="IP",
    params={"M": 16, "efConstruction": 128}
)
index_params.add_index(
    field_name="sparse_emb",
    index_type="SPARSE_INVERTED_INDEX",
    metric_type="BM25"
)

client.create_collection(
    collection_name=COLLECTION_NAME,
    schema=schema,
    index_params=index_params
)
print("✅ Milvus collection ready.")
