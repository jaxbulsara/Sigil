from distutils.core import setup

setup(
    name="neogm",
    packages=["neogm"],
    version="0.1",
    license="MIT",
    description="Object-Graph Mapper for the neo4j bolt driver for Python. Built for Python 3.",
    author="Jay Bulsara",
    author_email="jaxbulsara@gmail.com",
    url="https://github.com/jaxbulsara/neogm",
    download_url="https://github.com/jaxbulsara/neogm/archive/v0.1.tar.gz",
    keywords=["neo4j", "object-graph-mapper", "ogm", "bolt", "cypher"],
    install_requires=["neo4j",],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
    ],
)
