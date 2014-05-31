import setuptools

REQUIREMENTS = [
    "docopt==0.6.1",
    "Flask==0.10.1",
    "GitPython==0.3.2.RC1",
    "semantic_version==2.3.0",
]

if __name__ == "__main__":
    setuptools.setup(
        name="mypi",
        version="0.0.3",
        author="Sujay Mansingh",
        author_email="sujay.mansingh@gmail.com",
        packages=setuptools.find_packages(),
        include_package_data=True,
        scripts=[],
        url="https://github.com/sujaymansingh/mypi",
        license="LICENSE.txt",
        description="An api that can automatically build and serve python packages that are hosted on github",
        long_description="View the github page (https://github.com/sujaymansingh/mypi) for more details.",
        install_requires=REQUIREMENTS
    )
