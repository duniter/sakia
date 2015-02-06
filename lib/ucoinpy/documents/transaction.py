'''
Created on 2 déc. 2014

@author: inso
'''

from . import Document
import re
import logging

class Transaction(Document):
    '''
Document format :
Version: VERSION
Type: Transaction
Currency: CURRENCY_NAME
Issuers:
PUBLIC_KEY
...
Inputs:
INDEX:SOURCE:NUMBER:FINGERPRINT:AMOUNT
...
Outputs:
PUBLIC_KEY:AMOUNT
...
Comment: COMMENT
...


Compact format :
TX:VERSION:NB_ISSUERS:NB_INPUTS:NB_OUTPUTS:HAS_COMMENT
PUBLIC_KEY:INDEX
...
INDEX:SOURCE:FINGERPRINT:AMOUNT
...
PUBLIC_KEY:AMOUNT
...
COMMENT
SIGNATURE
...
    '''

    re_type = re.compile("Type: (Transaction)\n")
    re_header = re.compile("TX:([0-9]+):([0-9]+):([0-9]+):([0-9]+):(0|1)\n")
    re_issuers = re.compile("Issuers:\n")
    re_inputs = re.compile("Inputs:\n")
    re_outputs = re.compile("Outputs:\n")
    re_compact_comment = re.compile("([^\n]+)\n")
    re_comment = re.compile("Comment: ([^\n]*)\n")
    re_pubkey = re.compile("([1-9A-Za-z][^OIl]{42,45})\n")

    def __init__(self, version, currency, issuers, inputs, outputs,
                 comment, signatures):
        '''
        Constructor
        '''
        super().__init__(version, currency, signatures)

        self.issuers = issuers
        self.inputs = inputs
        self.outputs = outputs
        self.comment = comment

    @classmethod
    def from_compact(cls, currency, compact):
        lines = compact.splitlines(True)
        n = 0

        header_data = Transaction.re_header.match(lines[n])
        version = int(header_data.group(1))
        issuers_num = int(header_data.group(2))
        inputs_num = int(header_data.group(3))
        outputs_num = int(header_data.group(4))
        has_comment = int(header_data.group(5))
        n = n + 1

        issuers = []
        inputs = []
        outputs = []
        signatures = []
        for i in range(0, issuers_num):
            issuer = Transaction.re_pubkey.match(lines[n]).group(1)
            issuers.append(issuer)
            n = n + 1

        for i in range(0, inputs_num):
            input_source = InputSource.from_inline(lines[n])
            inputs.append(input_source)
            n = n + 1

        for i in range(0, outputs_num):
            output_source = OutputSource.from_inline(lines[n])
            outputs.append(output_source)
            n = n + 1

        comment = ""
        if has_comment == 1:
            comment = Transaction.re_compact_comment.match(lines[n]).group(1)
            n = n + 1

        while n < len(lines):
            signatures.append(Transaction.re_signature.match(lines[n]).group(1))
            n = n + 1

        return cls(version, currency, issuers, inputs, outputs, comment, signatures)

    @classmethod
    def from_signed_raw(cls, raw):
        lines = raw.splitlines(True)
        n = 0

        version = int(Transaction.re_version.match(lines[n]).group(1))
        n = n + 1

        Transaction.re_type.match(lines[n]).group(1)
        n = n + 1

        currency = Transaction.re_currency.match(lines[n]).group(1)
        n = n + 1

        issuers = []
        inputs = []
        outputs = []
        signatures = []

        if Transaction.re_issuers.match(lines[n]):
            n = n + 1
            while Transaction.re_inputs.match(lines[n]) is None:
                issuer = Transaction.re_pubkey.match(lines[n]).group(1)
                issuers.append(issuer)
                n = n + 1

        if Transaction.re_inputs.match(lines[n]):
            n = n + 1
            while Transaction.re_outputs.match(lines[n]) is None:
                input_source = InputSource.from_inline(lines[n])
                inputs.append(input_source)
                n = n + 1

        if Transaction.re_outputs.match(lines[n]) is not None:
            n = n + 1
            while not Transaction.re_comment.match(lines[n]):
                output = OutputSource.from_inline(lines[n])
                outputs.append(output)
                n = n + 1

        comment = Transaction.re_comment.match(lines[n]).group(1)
        n = n + 1

        if Transaction.re_signature.match(lines[n]) is not None:
            while n < len(lines):
                sign = Transaction.re_signature.match(lines[n]).group(1)
                signatures.append(sign)
                n = n + 1

        return cls(version, currency, issuers, inputs, outputs,
                   comment, signatures)

    def raw(self):
        doc = """Version: {0}
Type: Transaction
Currency: {1}
Issuers:
""".format(self.version,
                   self.currency)

        for p in self.issuers:
            doc += "{0}\n".format(p)

        doc += "Inputs:\n"
        for i in self.inputs:
            doc += "{0}\n".format(i.inline())

        doc += "Outputs:\n"
        for o in self.outputs:
            doc += "{0}\n".format(o.inline())

        doc += "Comment: "
        doc += "{0}\n".format(self.comment)

        return doc

    def compact(self):
        '''
        Return a transaction in its compact format.
        '''
        """TX:VERSION:NB_ISSUERS:NB_INPUTS:NB_OUTPUTS:HAS_COMMENT
PUBLIC_KEY:INDEX
...
INDEX:SOURCE:FINGERPRINT:AMOUNT
...
PUBLIC_KEY:AMOUNT
...
COMMENT
"""
        doc = "TX:{0}:{1}:{2}:{3}:{4}\n".format(self.version,
                                              len(self.issuers),
                                              len(self.inputs),
                                              len(self.outputs),
                                              '1' if self.comment != "" else '0')
        for pubkey in self.issuers:
            doc += "{0}\n".format(pubkey)
        for i in self.inputs:
            doc += "{0}\n".format(i.compact())
        for o in self.outputs:
            doc += "{0}\n".format(o.inline())
        if self.comment != "":
            doc += "{0}\n".format(self.comment)
        for s in self.signatures:
            doc += "{0}\n".format(s)

        return doc


class SimpleTransaction(Transaction):
    '''
As transaction class, but for only one issuer.
...
    '''
    def __init__(self, version, currency, issuer,
                 single_input, outputs, comment, signature):
        '''
        Constructor
        '''
        super().__init__(version, currency, [issuer], [single_input],
              outputs, comment, [signature])


class InputSource():
    '''
    A Transaction INPUT

    Compact :
    INDEX:SOURCE:FINGERPRINT:AMOUNT
    '''
    re_inline = re.compile("([0-9]+):(D|T):([0-9]+):\
([0-9a-fA-F]{5,40}):([0-9]+)\n")
    re_compact = re.compile("([0-9]+):(D|T):([0-9a-fA-F]{5,40}):([0-9]+)\n")

    def __init__(self, index, source, number, txhash, amount):
        self.index = index
        self.source = source
        self.number = number
        self.txhash = txhash
        self.amount = amount

    @classmethod
    def from_inline(cls, inline):
        data = InputSource.re_inline.match(inline)
        index = int(data.group(1))
        source = data.group(2)
        number = int(data.group(3))
        txhash = data.group(4)
        amount = int(data.group(5))
        return cls(index, source, number, txhash, amount)

    @classmethod
    def from_bma(cls, bma_data):
        index = None
        source = bma_data['type']
        number = bma_data['number']
        txhash = bma_data['fingerprint']
        amount = bma_data['amount']
        return cls(index, source, number, txhash, amount)

    def inline(self):
        return "{0}:{1}:{2}:{3}:{4}".format(self.index,
                                            self.source,
                                            self.number,
                                            self.txhash,
                                            self.amount)

    def compact(self):
        return "{0}:{1}:{2}:{3}".format(self.index,
                                        self.source,
                                        self.txhash,
                                        self.amount)


class OutputSource():
    '''
    A Transaction OUTPUT
    '''
    re_inline = re.compile("([1-9A-Za-z][^OIl]{42,45}):([0-9]+)")

    def __init__(self, pubkey, amount):
        self.pubkey = pubkey
        self.amount = amount

    @classmethod
    def from_inline(cls, inline):
        data = OutputSource.re_inline.match(inline)
        pubkey = data.group(1)
        amount = int(data.group(2))
        return cls(pubkey, amount)

    def inline(self):
        return "{0}:{1}".format(self.pubkey, self.amount)
