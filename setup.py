#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cyclone 异步Web框架 - PyPI发布配置
"""

import os
import re
from setuptools import setup, find_packages

# 读取版本号
def get_version():
    init_py = os.path.join(os.path.dirname(__file__), 'cyclone', '__init__.py')
    with open(init_py, 'r', encoding='utf-8') as f:
        content = f.read()
        version_match = re.search(r'^__version__ = [\'"]([^\'"]*)[\'"]', content, re.M)
        if version_match:
            return version_match.group(1)
    raise RuntimeError('Unable to find version string.')

# 读取长描述
def get_long_description():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    with open(readme_path, 'r', encoding='utf-8') as f:
        return f.read()

# 读取依赖
def get_requirements():
    requirements_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    with open(requirements_path, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name='cyclone-web',
    version=get_version(),
    author='0716gzs',
    author_email='J0716gzs@163.com',
    description='一个现代化的异步Web后端框架，基于协程和异步I/O',
    long_description=get_long_description(),
    long_description_content_type='text/markdown',
    url='https://github.com/0716gzs/Cyclone',
    packages=find_packages(),
    include_package_data=True,
    install_requires=get_requirements(),
    extras_require={
        'dev': [
            'pytest>=7.0.0',
            'pytest-asyncio>=0.21.0',
            'black>=23.0.0',
            'flake8>=6.0.0',
            'mypy>=1.0.0',
        ],
        'yaml': ['PyYAML>=6.0'],
        'redis': ['aioredis>=2.0.0'],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Framework :: AsyncIO',
        'Topic :: Internet :: WWW/HTTP :: HTTP Servers',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    keywords='async web framework http mysql asyncio coroutine',
    python_requires='>=3.8',
    entry_points={
        'console_scripts': [
            'cyclone=cyclone.cli:main',
        ],
    },
    project_urls={
        'Bug Reports': 'https://github.com/0716gzs/Cyclone/issues',
        'Source': 'https://github.com/0716gzs/Cyclone',
        'Documentation': 'https://github.com/0716gzs/Cyclone#readme',
    },
    zip_safe=False,
) 
