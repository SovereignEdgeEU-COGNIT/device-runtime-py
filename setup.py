from setuptools import find_packages, setup

setup(
    name="cognit",
    version="00.00.00",
    description="Cognit Device Runtime",
    author="IKERLAN",
    license="GPL",
    url="https://cognit.sovereignedge.eu/",
    include_package_data=True,
    packages=find_packages() + ["cognit.models", "cognit.modules", "cognit.test"],
    install_requires=[i.strip() for i in open("requirements.txt").readlines()],
    test_suite="cognit.test",
)
