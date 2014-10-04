#ucoin-python-api

A python implementation of [uCoin](https://github.com/ucoin-io/ucoin) API

## Requirements

In order to use the API, you have to first install the required dependencies given below thanks to pip:
 * requests

##Installation

Here is a fast installation procedure (a bit dirty) we suggest to quickly use this API.

```bash
$ mkdir $HOME/ucoin
$ cd $HOME/ucoin
$ git clone git@github.com:ucoin-io/ucoin-python-api.git ucoinpy
$ export PYTHONPATH="$HOME/ucoin:$PYTHONPATH"
```

Thus you are ready to use it with your own python program. Here is an example illustrating how to use it thanks to the python shell:

```python
In [1]: import ucoinpy as upy
In [2]: ch = upy.ConnectionHandler('ucoin.twiced.fr', 9101)
In [3]: upy.blockchain.Block(ch, 3).get()
Out[3]: 
{'membersChanges': [],
 'number': 3,
 'nonce': 1,
 'hash': '09813779721C1C6246DC54D2923B1AEEEDD792EF',
 'previousHash': '09B4C743268C36C59FEA30D3E8D81A4440A80981',
 'certifications': ['HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk:C4LcanvvGPwuJZofxRun6maux2qBLh2MTyq7rHnm24hD:1411716383:SajvOOKQ4DGG5IJKq3VK/BUxfVP4mRtcuYFx2Q2a2GPXbTrXAuWExiMlnctCO4zx8wgqWIyiS7X6CHkFEooeCA==',
  'C4LcanvvGPwuJZofxRun6maux2qBLh2MTyq7rHnm24hD:HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk:1411688856:kHYXaHZgYIdtDWpticJ+7wHI12onU74PgzeDSzpz1WDu1Xu+Oj5EexwxbO+bhWuiUqUJ4OjfMm6mHD+AWPUhBg=='],
 'signature': 'H+ZR3b+Y39b/gq59rjedQV89x991+B46C76CfG6STEdjADRU/BKgZ+UFEW04oblzbxmAYNvBXZw5vLoJYnzeAA==',
 'previousIssuer': 'HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk',
 'timestamp': 1411709213,
 'fees': None,
 'currency': 'beta_brousouf',
 'joiners': ['C4LcanvvGPwuJZofxRun6maux2qBLh2MTyq7rHnm24hD:CU8WNYGhOArn7aBCTvFb/rW9O+BpRSZcAfyVvynp+cWy5pFY1Ds7TtR/+fnwN35ub3garv1q6bKBsWt2yWegBA==:1411681631'],
 'excluded': [],
 'version': 1,
 'transactions': [],
 'identities': ['C4LcanvvGPwuJZofxRun6maux2qBLh2MTyq7rHnm24hD:CfC4O5IfW/01TZD3zxTzZfDllPZrpV44iFq/1T6D1mcUJfK7IDildLkqkI6W6/Hu/b5gU9QcJdnDFZh6WlmSDQ==:1411681459:moshe'],
 'leavers': [],
 'dividend': None,
 'issuer': 'HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk',
 'membersCount': 4}
```

Please take a look at the document [HTTP API](https://github.com/ucoin-io/ucoin/blob/master/doc/HTTP_API.md) to learn about the API.
