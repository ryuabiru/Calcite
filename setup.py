import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="calcite",
    version="0.1.1",
    author="R. Abiru",
    author_email="",
    description="A desktop application for data analysis and publication-quality graphing.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ryuabiru/calcite", # プロジェクトのGitHub URL
    
    # 'calcite'パッケージを自動で見つけるように設定
    packages=setuptools.find_packages(),
    
    # アプリケーションが依存するライブラリ
    install_requires=[
        "PySide6",
        "pandas",
        "numpy",
        "seaborn",
        "scipy",
        "statsmodels",
        "scikit-posthocs",
        "statannotations",
        "matplotlib"
    ],

    # 'calcite'コマンドでアプリを起動する
    entry_points={
        "console_scripts": [
            "calcite=calcite.main:plot",
        ],
    },
    
    # .py以外のファイル（ライセンスなど）を含める
    include_package_data=True,

    # パッケージの分類
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.10',
)
