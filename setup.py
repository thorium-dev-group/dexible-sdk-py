from distutils.core import setup

setup(name="dexible",
	  packages=["dexible", "dexible.abi"],
	  package_dir={
	  		"dexible": "src/dexible",
	  		"dexible.abi": "src/dexible/abi",
	  },
  	  package_data={
  	  		"dexible.abi": ["*.json"],
  	  },
  	  include_package_data=True,
	  version="1.1.0",
	  license="MIT",
	  description="Dexible SDK for Python",
	  long_description="Dexible is a fully automated Execution Management System for DeFi. In its simplest form, Dexible takes on the responsibility of executing DeFi \"orders\" according to user-specified \"policies\". Policies dictate how execution should be carried out. The SDK is a Python 3 library that gives developers and trade strategists a simple way of interacting with the Dexible infrastructure. From getting quotes, submitting orders, and querying for past orders, the SDK makes it easier to call the appropriate API endpoints with the proper signatures.",
	  author="BUIDLHub, Inc.",
	  author_email="support@buidlhub.com",
	  url="https://github.com/BUIDLHub/dexible-sdk-py",
	  download_url="https://github.com/BUIDLHub/dexible-sdk-py/archive/refs/tags/1.1.0.tar.gz",
	  keywords=["Finance", "Defi", "Ethereum", "Exchange"],
	  requires=[
	  		"web3",
	  		"aiohttp",
	  		"requests",
	  ],
	  classifiers=[
	  		"Development Status :: 5 - Production/Stable",
	  		"License :: OSI Approved :: MIT License",
	  		"Programming Language :: Python :: 3",
	  		"Programming Language :: Python :: 3.5",
	  		"Programming Language :: Python :: 3.6",
	  		"Programming Language :: Python :: 3.7",
	  		"Programming Language :: Python :: 3.8",
	  		"Programming Language :: Python :: 3.9",
	  		"Programming Language :: Python :: 3.10",
	  ],
	  python_requires=">=3.5",
)
