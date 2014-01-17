import hashlib, re
from pprint import pprint

class Merkle:
    """
    class to create a Merkle Tree.

    Here is the example we want that it works:

    >>> tree = Merkle('abcde').process()
    >>> tree.root()
    '114B6E61CB5BB93D862CA3C1DFA8B99E313E66E9'
    >>> tree.depth()
    3
    >>> tree.levels()
    4
    >>> tree.nodes()
    6
    >>> tree.level(0)
    ['114B6E61CB5BB93D862CA3C1DFA8B99E313E66E9']
    >>> tree.level(1)
    ['585DD1B0A3A55D9A36DE747EC37524D318E2EBEE', '58E6B3A414A1E090DFC6029ADD0F3555CCBA127F']
    >>> tree.level(2)
    ['F4D9EEA3797499E52CC2561F722F935F10365E40', '734F7A56211B581395CB40129D307A0717538088', '58E6B3A414A1E090DFC6029ADD0F3555CCBA127F']
    """

    def __init__(self, strings, hashfunc=hashlib.sha1):
        """ctor enables to set a list of strings used to process merkle tree and set the hash function

        Arguments:
        - `strings`: list of strings
        - `hashfunc`: hash function
        """

        self.strings = strings
        self.hashfunc = hashfunc

        self.leaves = []
        self.tree_depth = 0
        self.rows = []
        self.nodes_count = 0

        for s in strings: self.feed(s)

    def feed(self, anydata):
        """add a new string into leaves

        Arguments:
        - `anydata`: new string
        """

        if anydata and re.match(r'^[\w\d]{40}$', anydata):
            self.leaves.append(anydata.upper())
        else:
            self.leaves.append(self.hashfunc(anydata.encode('ascii')).hexdigest().upper())

        return self

    def depth(self):
        """computes and returns the depth value"""

        if not self.tree_depth:
            power = 0
            while 2**power < len(self.leaves):
                power += 1
            self.tree_depth = power

        return self.tree_depth

    def levels(self):
        """returns the number of levels"""

        return self.depth()+1

    def nodes(self):
        """returns the number of nodes"""

        self.process()
        return self.nodes_count

    def process(self):
        """computes the merkle tree thanks to the data fullfilled in leaves"""

        d = self.depth()
        if not len(self.rows):
            for i in range(d): self.rows.append([])
            self.rows.append(self.leaves)
            for i in reversed(range(d)):
                self.rows[i] = self.__get_nodes__(self.rows[i+1])
                self.nodes_count += len(self.rows[i])

        return self

    def root(self):
        """returns the root node of the tree"""

        return self.rows[0][0]

    def level(self, i):
        """returns a level thanks to the level number passed in argument

        Arguments:
        - `i`: level number
        """

        return self.rows[i]

    def __get_nodes__(self, leaves):
        """Compute nodes for a specific level. This method is private and used in intern from process method.

        Arguments:
        - `leaves`: set of nodes to process
        """

        class List(list):
            """Wrapper to enable to define what ever index you want even if the size doesnot fit yet."""

            def __setitem__(self, index, value):
                if index >= len(self):
                    for _ in range(index-len(self)+1):
                        self.append(None)
                super().__setitem__(index, value)

        l = len(leaves)
        r = l % 2
        nodes = List()
        for i in range(0, l-1, 2):
            nodes[int(i/2)] = self.hashfunc((leaves[i] + leaves[i+1]).encode('ascii')).hexdigest().upper()
        if r == 1:
            nodes[int((l-r)/2)] = leaves[l-1]
        return nodes
