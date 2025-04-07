from setuptools import setup, find_packages

setup(
    name="usdc-terminal",  # Name of your package
    version="0.1.0",  # Initial version
    packages=find_packages(),
    install_requires=[
        "pandas",
        "numpy",
        "web3",
        "requests",
        "python-dotenv",
        "click",
        "twilio",
        "cachetools"
    ],
    extras_require={
        "fiat-ramps": ["flask", "requests"],
        "scheduler": ["apscheduler", "flask"],
        "all": ["flask", "requests", "apscheduler"]
    },
    entry_points={
        "console_scripts": [
            "usdc-terminal=cli:cli"
        ]
    },
    author="Brandyn Hamilton",
    author_email="brandynham1120@gmail.com",
    description="Simple Cross-Chain USDC Transfers Powered by CCIP",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url=" ",  # optional
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",  # or whatever license
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)
