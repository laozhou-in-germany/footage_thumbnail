import os
from setuptools import setup, find_packages

setup(
    name="footage-thumbnailer",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "opencv-python>=4.8.0",
        "ffmpeg-python>=0.2.0",
        "Pillow>=10.0.0",
        "customtkinter>=5.2.0",
    ],
    entry_points={
        "console_scripts": [
            "footage-thumbnailer=src.main:main",
        ],
    },
    author="Footage Thumbnailer Team",
    description="Generate visual contact sheets from video collections",
    long_description=open("README.md").read() if os.path.exists("README.md") else "",
    long_description_content_type="text/markdown",
    python_requires=">=3.9",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Multimedia :: Video",
        "Topic :: Utilities",
    ],
)