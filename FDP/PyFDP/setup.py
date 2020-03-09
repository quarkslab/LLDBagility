import setuptools

setuptools.setup(
    name="PyFDP",
    version="20.0",
    packages=setuptools.find_packages(),
    package_data={"PyFDP": ["libFDP.dylib"],},
    url="https://github.com/quarkslab/LLDBagility",
)
