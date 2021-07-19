from setuptools import setup

setup(
    name='jsonrpc2',
    version='1.4.8',
    url='https://gitlab.com/mburkard/jsonrpc2',
    license='Custom',
    author='Matthew Burkard',
    author_email='matthewjburkard@gmail.com',
    description='Python implementation of JSON RPC 2.0 specification.',
    packages=['jsonrpc2'],
    long_description_content_type='text/markdown',
    long_description=open('README.md').read(),
    classifiers=['Programming Language :: Python :: 3'],
    zip_safe=False
)
