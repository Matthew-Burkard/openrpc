from setuptools import setup

setup(
    name='openrpc',
    version='3.0.2',
    url='https://gitlab.com/mburkard/openrpc',
    license='Custom',
    author='Matthew Burkard',
    author_email='matthewjburkard@gmail.com',
    description='Python implementation of the OpenRPC specification.',
    packages=['openrpc'],
    long_description_content_type='text/markdown',
    long_description=open('README.md').read(),
    classifiers=['Programming Language :: Python :: 3'],
    zip_safe=False
)
