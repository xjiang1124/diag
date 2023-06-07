mkdir $1
echo "import sys, os" > $1/$1.py
echo "" >> $1/$1.py
echo "sys.path.append(os.path.relpath(\"../../lib\"))" >> $1/$1.py
echo "import libtest_config" >> $1/$1.py
echo "" >> $1/$1.py
echo "param_cfg = libtest_config.parse_config(\"lib/tests/$1/parameters.yaml\")" >> $1/$1.py
echo "" >> $1/$1.py

echo "- Test: $1" > $1/parserules.yaml

echo "  Name: $1" > $1/parameters.yaml
echo "  Description: " >> $1/parameters.yaml

echo "from .$1 import $1" >> __init__.py
