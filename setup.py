from setuptools import find_packages, setup

# Read requirements from files
with open("requirements.txt") as f:
    requirements = f.read().splitlines()

with open("requirements-dev.txt", "r", encoding="utf-8") as f:
    dev_requirements = f.read().splitlines()

setup(
    name="libsync",
    version="0.1.0",
    packages=find_packages(exclude=["tests*"]),
    install_requires=requirements,
    extras_require={
        "dev": dev_requirements,
    },
    author="Josh Lebedinsky",
    author_email="joshlebed@gmail.com",
    description="A collection of tools for managing your music library",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/joshlebed/libsync",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.10",
)
