from setuptools import setup, find_packages

setup(
    name="wesmol-indexer",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "web3>=6.0.0",
        "msgspec>=0.18.0",
        "sqlalchemy>=2.0.0",
        "google-cloud-storage>=2.0.0",
        "python-dotenv>=1.0.0",
        "flask>=2.0.0",
        "tqdm>=4.65.0",
        "requests>=2.28.0",
        "functions-framework>=3.0.0",
        "psycopg[binary]>=3.0.0"
    ]
)