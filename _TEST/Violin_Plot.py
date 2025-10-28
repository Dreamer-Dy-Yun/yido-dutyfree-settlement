import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

# Qdrant에서 꺼낸 벡터 리스트 (예시)
vectors = [
    [0.1, 0.3, 0.25, 1, 1, 0],
    [0.2, 0.5, 0.35, 0, 0, 0],
    [0.15, 0.4, 0.30, 0, 0, 0]
]

data = np.array(vectors)

# 시각화
sns.violinplot(data=data)
plt.xlabel("measured point")
plt.ylabel("normalized value")
plt.show()
