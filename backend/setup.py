from setuptools import setup, find_packages

setup(
    name='NOVAS_EZ_Project',
    version='0.2',
    packages=find_packages(),  # CUSTOMIZED등 자동 인식
)

#  루트폴더에서 실행
# pip install -e .
# 패키지 업데이트 시 루트폴더에서 실행
# pip install -e . --upgrade