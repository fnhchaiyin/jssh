import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="jssh", # Replace with your own username
    version="4.0.8",
    author="jhy",
    author_email="fnhchaiying@163.com",
    description="GUI,ssh to multiple servers",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/fnhchaiyin/jssh",
    packages=setuptools.find_packages(),
    #packages={'jssh'},
    classifiers=[
        "Programming Language :: Python :: 2.7",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=['paramiko'],
    entry_points={
    'console_scripts': [
        'jssh = jssh.jssh:main',
    ],
    },
    include_package_data=True,
)