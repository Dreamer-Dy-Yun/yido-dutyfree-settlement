# Possibility Mass Function 그래프
import matplotlib.pyplot as plt
from collections import Counter

x = [1, 2, 2, 3, 3, 3, 4, 5, 4, 1,1,1,2,2,2,2,2,2,2,3,9,9,9,9,9,9,9,9,9,9,9]
# 빈도수 계산
count = Counter(x)
total = sum(count.values())

# 전체 x축 범위 정의 (min~max)
x_full = range(min(x), max(x) + 1)  # 여기선 1~9

# 제로 패딩 PMF 생성
pmf = {k: count.get(k, 0) / total for k in x_full}

# 그래프 출력
plt.stem(list(pmf.keys()), list(pmf.values()))
plt.title("Probability Mass Function (PMF) with Zero Padding")
plt.xlabel("Value")
plt.ylabel("Probability")
plt.ylim(0, 1)
plt.show()

input("Press Enter to continue...")
