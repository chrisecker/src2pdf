#!/usr/bin/env python

from distutils.core import setup

setup(name='src2pdf',
      version='0.0',
      description='A source code to pdf formatter.',
      author='C. Ecker',
      author_email='textmodelview@gmail.com',
      scripts=['src/src2pdf'],
      url='https://github.com/chrisecker/src2pdf',
      license='BSD',
      install_requires=[
          'entrypoint2',
          'pygments',
      ],      
)
