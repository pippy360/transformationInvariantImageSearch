#!/usr/bin/env python
from setuptools import setup, find_packages


def readme():
    with open('README.md') as f:
        return f.read()

setup(
    name='transformation-invariant-image-search',
    version='0.0.1',
    description='a reverse image search algorithm which performs 2D affine '
    'transformation-invariant partial image-matching in sublinear time with '
    'respect to the number of images in our database.',
    long_description=readme(),
    long_description_content_type="text/markdown",
    author='Tom Murphy',
    author_email='murphyt7@tcd.ie',
    maintainer='Rachmadani Haryono',
    maintainer_email='foreturiga@gmail.com',
    license='MIT',
    url='https://github.com/pippy360/transformationInvariantImageSearch',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    python_requires='>=3.6',
    install_requires=[
        'appdirs>=1.4.3',
        'Flask-Admin==1.5.3',
        'Flask-SQLAlchemy>=2.3.2',
        'Flask>=1.0.2',
        'hiredis',
        'numpy',
        'opencv-python>=4.0.0.21',
        'Pillow>=5.4.1',
        'redis',
        'scikit-learn',
        'scipy',
        'SQLAlchemy-Utils>=0.33.11',
        'tqdm>=4.29.1',
    ],
    extras_require={
        'dev': [
            'docutils==0.14',
            'pytest==4.2.0',
        ],
    },
    entry_points={
        'console_scripts': [
            'transformation-invariant-image-search = transformation_invariant_image_search.main:cli']
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
