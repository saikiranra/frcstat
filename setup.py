from setuptools import setup, find_packages

NAME = "frcstat"
VERSION = "0.1"
LICENSE = "MIT"
AUTHOR = "Saikiran Ramanan"
EMAIL = "saikiranra@gmail.com"
DESCRIPTION = "FRC Statistics Library using TBA to pull data"
PACKAGES = ["frcstat" , "tests"]
REQUIRES = ["numpy" , "scipy" , "requests"]



setup(name=NAME,
    version=VERSION, 
    license=LICENSE,
    author=AUTHOR,
    author_email=EMAIL,
    description=DESCRIPTION, 
    packages=PACKAGES,
    install_requires=REQUIRES
)
