# usfm-tools
Tools for converting, cleaning, and checking Scripture text

## How to use
To get the graphical interface, you can run `usfm_wizard.py` in the `src/` directory using `python usfm_wizard.py`. You may need to install some dependencies first.

### Virtual Environments
If you want to use USFM Tools without changing your normal python environment, you can use `python -m` to create a virtual environment where you can install the dependencies separate from your normal python environment. For example, you could use `python -m wizard ./wizard` to create a python virtual environment called **wizard** in your current directory.
Then, use `source wizard/bin/activate` or `wizard\\Scripts\\activate.bat` on Windows.

https://anaconda.com also has a product that can make it easier to create and use virtual environments.

## Requirements
- Python 3.10 or later
- json
- jsonschema
- python-docx
- pyyaml
- requests

You may be able to install these with `pip install python-docx pyyaml requests`
