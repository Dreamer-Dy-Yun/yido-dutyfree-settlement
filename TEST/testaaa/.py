import json

json_file = open(r"C:\Users\user\Downloads\response_1762391608093.json", "r", encoding="utf-8").read()
json_data = json.loads(json_file)


print(json_data["06DB9205606EDVNAY990076"]["list_measured"] == json_data["06DB9205606EDVNAY990122"]["list_measured"])
print(json_data["06DB9205606EDVNAY990172"]["list_measured"] == json_data["06DB9205606EDVNAY990122"]["list_measured"])
print(json_data["06DB9205606EDVNAY990193"]["list_measured"] == json_data["06DB9205606EDVNAY990122"]["list_measured"])
print(json_data["06DB9205606EDVNAY990180"]["list_measured"] == json_data["06DB9205606EDVNAY990122"]["list_measured"])

# for key, value in json_data.items():
#     print(key)

# 06DB9205606EDVNAY990076
# 06DB9205606EDVNAY990122
# 06DB9205606EDVNAY990172
# 06DB9205606EDVNAY990193
# 06DB9205606EDVNAY990180

# for key, value in json_data["06DB9205606EDVNAY990076"].items():
#     print(key)

# serial_query
# measured_id
# instrument_name
# model_name
# serial_result
# measured_at
# rank
# distance
# vector_visual_normed
# list_measured


