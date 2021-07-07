from setuptools import setup

setup(
    name='json-rpc2',
    version='1.2.3',
    url='https://gitlab.com/mburkard/json-rpc2',
    license='Custom',
    author='Matthew Burkard',
    author_email='matthewjburkard@gmail.com',
    description='Python implementation of JSON RPC 2.0 specification.',
    packages=['jsonrpc2'],
    long_description_content_type='text/markdown',
    long_description=open('README.md').read(),
    classifiers=[
        'Programming Language :: Python :: 3',
    ],
    zip_safe=False
)
