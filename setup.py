#!/usr/bin/env python
from setuptools import setup, find_packages

"""
TODO
- copy or link `python` folder to `transformation_invariant_image_search`
"""

setup(
    name='transformation-invariant-image-search',
    version='0.0.1',
    description='a reverse image search algorithm which performs 2D affine '
    'transformation-invariant partial image-matching in sublinear time with '
    'respect to the number of images in our database.',
    #  long_description=,  # TODO
    long_description_content_type="text/markdown",
    #  author='Tom Murphy',  # TODO, author, must be with author_email
    #  author_email='',  # TODO
    maintainer='Rachmadani Haryono',
    maintainer_email='foreturiga@gmail.com',
    license='MIT',
    url='https://github.com/pippy360/transformationInvariantImageSearch',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    python_requires='>=3.5',
    install_requires=[
        'hiredis',
        'numpy',
        'redis',
        'scikit-learn',
        'scipy',
        'tqdm>=4.29.1',
    ],
    entry_points={
        'console_scripts': [
            'transformation-invariant-image-search = transformation_invariant_image_search.main:main']
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Internet :: WWW/HTTP :: Indexing/Search',
        'Topic :: Utilities'
    ]
)
