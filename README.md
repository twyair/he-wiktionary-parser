# he-wiktionary-parser

### how to use

1. download the dump (in xml) of the hebrew wiktionary from [here](https://dumps.wikimedia.org/)
2. clone this repo
3. in python
```python
from parse import parse_pages
pages = parse_pages("path/to/wiktionary/dump.xml")
```
