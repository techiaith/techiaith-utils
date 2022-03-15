from setuptools import setup, find_namespace_packages


packages = find_namespace_packages('src')

setup(
    name='techiaith-utils',
    version='v22.03',
    packages=packages,
    package_dir={'': 'src'},
    include_package_data=True,
    install_requires=[
        'lxml>=4.8.0',
        'requests>=2.27.1',
        'sacremoses>=0.0.47',
        'translate-toolkit>=3.6.0',
        'tqdm>=4.63.0'
    ],
    extras_require={
        'dev': ['gitpython', 'virtualenvwrapper', 'pytest']
    })
