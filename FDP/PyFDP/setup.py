import setuptools

setuptools.setup(
    name="PyFDP",
    version="20.1",
    packages=setuptools.find_packages(),
    package_data={"PyFDP": ["libFDP.dylib"],},
)
