from setuptools import find_packages, setup

setup(
    name='brigitte',
    version='0.2',
    packages=find_packages(exclude=['brigitte_site', 'brigitte_site.*']),
    zip_safe=False,
)
