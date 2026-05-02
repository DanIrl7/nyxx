# Package Name
# Version (1.0)
# Description (the one you gave me earlier)
# Author info
# Python version requirement
import setuptools

setuptools.setup(
    name="navii",
    version="1.0",
    description="Navii makes navigating the terminal easier and more intuitive. With the navii command and the arrow keys, you can navigate to any file or directory in you system in a few seconds, save your most used paths, and more.",
    author="Daniel Masona",
    author_email="danielmasona7@gmail.com",
    packages=setuptools.find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
)