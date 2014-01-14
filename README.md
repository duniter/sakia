#ucoin-python-api

A python implementation of [uCoin](https://github.com/c-geek/ucoin) API

##Installation

Here is a fast installation procedure (a bit dirty) we suggest to quickly use this API.

```bash
$ cd $HOME
$ git clone git@github.com:canercandan/ucoin-python-api.git
$ export PYTHONPATH="$HOME/ucoin-python-api:$PYTHONPATH"
```

Thus you are ready to use it with your own python program. Here is an example illustrating how to use it thanks to the python shell:

```python
import ucoin
ucoin.ucg.Peering().get()
```

Please take a look at the document [HTTP API](https://github.com/c-geek/ucoin/blob/master/doc/HTTP_API.md) to learn about the API.
