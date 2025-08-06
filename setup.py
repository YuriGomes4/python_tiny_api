from setuptools import setup

with open("README.md", "r") as arq:
    readme = arq.read()

setup(name='py_tiny',
    version='0.0.6',
    license='MIT License',
    author='Yuri Gomes',
    long_description=readme,
    long_description_content_type="text/markdown",
    author_email='yurialdegomes@gmail.com',
    keywords='tiny',
    description=u'Wrapper não oficial do Tiny V2',
    packages=['py_tiny'],
    install_requires=['requests'],)