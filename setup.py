from setuptools import setup, find_packages

# Read the README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="mistrs",
    version="0.1.1",
    author="Rory Standage",
    description="A library of basic functions to communicate with Mist API",
    url="https://github.com/rstandage/mistrs",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    python_requires=">=3.6",  # Minimum Python version
    install_requires=[
        "pandas<=2.2.3",
        "prettytable<=3.14.0",
        "requests>=2.25.0",
        "urllib3>=1.26.0"
    ],
)