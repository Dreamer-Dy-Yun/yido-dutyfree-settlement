import numpy as np


values = [55.3325, 71.8037, 60.2763, 54.4883, 42.3655, 64.5894, 43.7587, 89.1773, 96.3663, 38.3442,
 79.1725, 52.8895, 56.8045, 92.5597, 7.1036, 8.7129, 2.0218, 83.2619, 77.8157, 87.0012,
 97.8618, 79.9159, 46.1479, 78.0529, 11.8274, 63.9938, 14.3353, 94.4669, 52.1848, 41.4662,
 26.4556, 77.4234, 45.6150, 56.8434, 1.8789, 61.7636, 61.2096, 61.6934, 94.3748, 68.1820,
 35.9508, 43.7032, 69.7631, 6.0225, 66.6767, 67.0638, 21.0383, 12.8926, 46.1543, 60.2763,
 6.6524, 66.6767, 31.7983, 41.4263, 69.2916, 57.0197, 43.8602, 43.7032, 20.8877, 25.1321,
 66.6767, 19.6582, 36.8725, 82.0993, 9.7101, 83.7945, 9.6098, 97.6459, 46.8651, 97.6761,
 60.4846, 73.9264, 3.9188, 28.2807, 12.0197, 29.6140, 11.8728, 31.7983, 41.7410, 7.8053,
 1.1827, 58.6513, 61.2096, 13.8183, 19.7742, 44.7125, 3.8344, 5.8120, 55.6814, 12.0197,
 38.3442, 29.1229, 56.8045, 1.2893, 61.6934, 96.3663, 94.3748, 97.6459, 3.9188, 20.8877]


# NumPy 배열로 변환
values_np = np.array(values)

# 클리핑 ( = 클램핑)
quantized = np.clip(values_np, 10, 90)

# 25등분: 각 구간 길이는 4
quantized = np.floor(quantized / 10).astype(int) + 1


# 결과 확인
print(quantized.tolist())


# ##############################################################################
import numpy as np
import matplotlib.pyplot as plt
from collections import Counter

# # 값 정의
# values = [...]  # 입력 생략. 위에서 제공하신 리스트 사용
# values_np = np.array(values)

# # 25구간 양자화 (1~25)
# quantized = np.floor(values_np / 4).astype(int) + 1
# quantized = np.clip(quantized, 1, 25)

# 빈도 계산
counts = Counter(quantized)
total = sum(counts.values())
max_value = int(max(counts))
# PMF 정의 (빈 값은 0으로)
pmf = {k: counts.get(k, 0) / total for k in range(-5, max_value + 1)}

# 시각화
plt.figure(figsize=(10, 4))
plt.stem(list(pmf.keys()), list(pmf.values()))
plt.title("Probability Mass Function (PMF) with Zero Padding")
plt.xlabel("Quantized Bin (1–25)")
plt.ylabel("Probability")
plt.xticks(range(-5,max_value + 1))
plt.ylim(0, max(pmf.values()) * 1.0)
plt.grid(True, axis='y', linestyle='--', alpha=0.5)
plt.show()



