from setuptools import setup, find_packages
import lamp

setup(
    name='lamp',
    version=lamp.__version__,
    packages=find_packages(),
    license='MIT',
    description='lamp client',
    long_description=open('README.txt').read(),
    install_requires=['Pillow', 'asyncio'],
    url='https://github.com/balashovartem/lamp',
    author='Balashov Artem',
    author_email='balashov.artem@gmail.com',
    entry_points={'console_scripts': ['lamp = lamp.lamp:main']},
    package_data={'lamp': ['*.png']},
)
