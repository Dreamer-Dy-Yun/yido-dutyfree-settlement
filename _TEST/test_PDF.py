# Possibility Density Function 그래프
import numpy as np
from scipy.stats import gaussian_kde
import matplotlib.pyplot as plt

data = np.array([1, 2, 2, 3, 3, 3, 4, 5, 4, 1,1,1,2,2,2,2,2,2,2,3,9,9,9,9,9,9,9,9,9,9,9])

kde = gaussian_kde(data)
x_vals = np.linspace(0, 10, 500)
pdf = kde(x_vals)

plt.plot(x_vals, pdf)
plt.title("PDF (KDE)")
plt.xlabel("x")
plt.ylabel("Density")
plt.show()
input("Press Enter to continue...")