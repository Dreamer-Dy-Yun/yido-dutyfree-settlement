from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

# 1. Qdrant 서버 연결
client = QdrantClient(host="localhost", port=6333)

# 2. 컬렉션 생성 (벡터 길이 = 4, 코사인 유사도 사용)
client.recreate_collection(
    collection_name="sensor_data",
    vectors_config=VectorParams(size=4, distance=Distance.COSINE)
)

# 3. 벡터 데이터 삽입 (id는 고유값, payload는 메타데이터)
client.upsert(
    collection_name="sensor_data",
    points=[
        PointStruct(id=1, vector=[0.1, 0.2, 0.3, 0.4], payload={"serial_no": "ABC123"}),
        PointStruct(id=2, vector=[0.9, 0.8, 0.7, 0.6], payload={"serial_no": "DEF456"}),
        PointStruct(id=3, vector=[0.3273, 0.4162, 0.7316, 0.7286], payload={"serial_no": "SN00003"}),
        PointStruct(id=4, vector=[0.7192, 0.1444, 0.1541, 0.3987], payload={"serial_no": "SN00004"}),
        PointStruct(id=5, vector=[0.3017, 0.0619, 0.7162, 0.2631], payload={"serial_no": "SN00005"}),
        PointStruct(id=6, vector=[0.3174, 0.9655, 0.5487, 0.1305], payload={"serial_no": "SN00006"}),
        PointStruct(id=7, vector=[0.6549, 0.9844, 0.6472, 0.4918], payload={"serial_no": "SN00007"}),
        PointStruct(id=8, vector=[0.127, 0.5575, 0.6365, 0.7497], payload={"serial_no": "SN00008"}),
        PointStruct(id=9, vector=[0.0457, 0.9675, 0.9116, 0.327], payload={"serial_no": "SN00009"}),
        PointStruct(id=10, vector=[0.9068, 0.1155, 0.5597, 0.395], payload={"serial_no": "SN00010"}),
        PointStruct(id=11, vector=[0.8799, 0.9622, 0.0556, 0.2947], payload={"serial_no": "SN00011"}),
        PointStruct(id=12, vector=[0.9469, 0.0589, 0.6463, 0.0655], payload={"serial_no": "SN00012"}),
        PointStruct(id=13, vector=[0.4213, 0.8705, 0.7357, 0.2755], payload={"serial_no": "SN00013"}),
        PointStruct(id=14, vector=[0.3241, 0.3211, 0.8893, 0.0183], payload={"serial_no": "SN00014"}),
        PointStruct(id=15, vector=[0.0214, 0.3608, 0.2776, 0.5294], payload={"serial_no": "SN00015"}),
        PointStruct(id=16, vector=[0.2132, 0.3051, 0.2774, 0.5073], payload={"serial_no": "SN00016"}),
        PointStruct(id=17, vector=[0.2973, 0.1223, 0.7753, 0.6625], payload={"serial_no": "SN00017"}),
        PointStruct(id=18, vector=[0.3018, 0.1403, 0.2872, 0.7757], payload={"serial_no": "SN00018"}),
        PointStruct(id=19, vector=[0.7556, 0.2968, 0.2301, 0.9225], payload={"serial_no": "SN00019"}),
        PointStruct(id=20, vector=[0.4792, 0.4765, 0.6898, 0.7795], payload={"serial_no": "SN00020"}),
        PointStruct(id=21, vector=[0.4434, 0.0133, 0.2709, 0.049], payload={"serial_no": "SN00021"}),
        PointStruct(id=22, vector=[0.5056, 0.9117, 0.0032, 0.6056], payload={"serial_no": "SN00022"}),
        PointStruct(id=23, vector=[0.8426, 0.1186, 0.9112, 0.6668], payload={"serial_no": "SN00023"}),
        PointStruct(id=24, vector=[0.8975, 0.5527, 0.6988, 0.378], payload={"serial_no": "SN00024"}),
        PointStruct(id=25, vector=[0.6941, 0.0077, 0.9749, 0.7227], payload={"serial_no": "SN00025"}),
        PointStruct(id=26, vector=[0.2769, 0.3832, 0.1097, 0.6468], payload={"serial_no": "SN00026"}),
        PointStruct(id=27, vector=[0.8775, 0.3909, 0.6814, 0.446], payload={"serial_no": "SN00027"}),
        PointStruct(id=28, vector=[0.6551, 0.8594, 0.5324, 0.3329], payload={"serial_no": "SN00028"}),
        PointStruct(id=29, vector=[0.8129, 0.2712, 0.9379, 0.9222], payload={"serial_no": "SN00029"}),
        PointStruct(id=30, vector=[0.0921, 0.7016, 0.0475, 0.8552], payload={"serial_no": "SN00030"})
    ]
)

# 4. 유사도 검색 (가장 가까운 1개 검색)
hits = client.search(
    collection_name="sensor_data",
    query_vector=[0.5050, 0.9120, 0.0030, 0.6054],
    limit=3
)

# 5. 결과 출력
for hit in hits:
    print("🔍 ID:", hit.id)
    print("📐 Score (유사도):", hit.score)
    print("📦 Payload:", hit.payload)
    print("📦 shard_key:", hit.shard_key)