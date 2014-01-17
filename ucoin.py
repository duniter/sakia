#!/usr/bin/env python3
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Authors:
# Caner Candan <caner@candan.fr>, http://caner.candan.fr
#

from pprint import pprint
import ucoin, json, logging, argparse, sys, gnupg, hashlib, re
from collections import OrderedDict

logger = logging.getLogger("cli")

# def action_transactions():
#     for tx in ucoin.hdc.transactions.All().get():
#         print(tx['hash'])

def print_amendment(am):
    print("""\
Version\t\t\t%(version)s
Currency\t\t%(currency)s
Number\t\t\t%(number)s
GeneratedOn\t\t%(generated)s
UniversalDividend\t%(dividend)s
NextRequiredVotes\t%(nextVotes)s
PreviousHash\t\t%(previousHash)s
MembersRoot\t\t%(membersRoot)s
MembersCount\t\t%(membersCount)s\
    """ % am)

    if am['membersChanges']:
        print('MembersChanges')
        for x in am['membersChanges']: print(x)

    print("""\
VotersRoot\t\t%(votersRoot)s
VotersCount\t\t%(votersCount)s\
    """ % am)

    if am['votersChanges']:
        print('VotersChanges')
        for x in am['votersChanges']: print(x)

def current():
    logger.debug('current')

    print_amendment(ucoin.hdc.amendments.Current().get())

def contract():
    logger.debug('contract')

    print("""\
-----------------------------------
-             CONTRACT            -
-----------------------------------\
    """)

    for am in ucoin.hdc.amendments.List().get():
        print_amendment(am)
        print('------------------------------------')

def lookup():
    logger.debug('lookup')

    print(ucoin.pks.Lookup().get(search=ucoin.settings['search'], op='get'))

def peering():
    logger.debug('peering')

    peer = ucoin.ucg.Peering().get()

    __dict = {}
    for d in [peer, peer['contract'], peer['merkles']['pks/all'], peer['remote'],]:
        __dict.update(d)

    print("""\
Currency\t%(currency)s
Public key FPR\t%(key)s
Contract\t%(currentNumber)s-%(hash)s
Public keys\t%(leavesCount)d
Remote host\t%(host)s\
    """ % __dict)

    if __dict['ipv4']: print('Remote ipv4\t%(ipv4)s' % __dict)
    if __dict['ipv6']: print('Remote ipv6\t%(ipv6)s' % __dict)

    print("""\
Remote port\t%(port)d\
    """ % __dict)

def pubkey():
    logger.debug('pubkey')

    print(ucoin.ucg.Pubkey().get())

def index():
    logger.debug('index')

    __dict = ucoin.hdc.amendments.Votes().get()['amendments']

    i = 0
    while True:
        if str(i) not in __dict: break
        for k,v in __dict[str(i)].items():
            print('%d-%s:%d' % (i, k, v))
        i += 1

def issue():
    logger.debug('issue')

    try:
        last_tx = ucoin.hdc.transactions.sender.Last(ucoin.settings['fingerprint']).get()
    except ValueError:
        last_tx = None

    try:
        last_issuance = ucoin.hdc.transactions.sender.issuance.Last(ucoin.settings['fingerprint']).get()
    except ValueError:
        last_issuance = None

    __dict = {}
    __dict.update(ucoin.settings)
    __dict['version'] = 1
    __dict['number'] = 0 if not last_tx else last_tx['transaction']['number']+1
    __dict['previousHash'] = hashlib.sha1(("%(raw)s%(signature)s" % last_tx).encode('ascii')).hexdigest().upper()
    __dict['type'] = 'ISSUANCE'

    # pprint(__dict)

    tx = """\
Version: %(version)d
Currency: %(currency)s
Sender: %(fingerprint)s
Number: %(number)d
""" % __dict

    if last_tx: tx += "PreviousHash: %(previousHash)s\n" % __dict

    tx += """\
Recipient: %(fingerprint)s
Type: %(type)s
Coins:
""" % __dict

    def get_next_coin_number(coins):
        number = 0
        for c in coins:
            candidate = int(c['id'].split('-')[1])
            if candidate > number: number = candidate
        return number+1

    previous_idx = 0 if not last_issuance else get_next_coin_number(last_issuance['transaction']['coins'])

    for idx, coin in enumerate(ucoin.settings['coins']):
        __dict['idx'] = idx+previous_idx
        __dict['base'], __dict['power'] = [int(x) for x in coin.split(',')]
        tx += '%(fingerprint)s-%(idx)d-%(base)d-%(power)d-A-%(amendment)d\n' % __dict

    tx += """\
Comment:
%(message)s
""" % __dict

    tx = tx.replace("\n", "\r\n")
    txs = ucoin.settings['gpg'].sign(tx, detach=True, keyid=ucoin.settings['user'])

    try:
        ucoin.hdc.transactions.Process().post(transaction=tx, signature=txs)
    except ValueError as e:
        print(e)
    else:
        print('Posted issuance transaction')

def transfer():
    logger.debug('transfer')
    logger.debug('recipient: %s' % ucoin.settings['recipient'])

    if not ucoin.settings['coins']: ucoin.settings['coins'] = input()

    logger.debug('coins: %s' % ucoin.settings['coins'])

    try:
        last_tx = ucoin.hdc.transactions.sender.Last(ucoin.settings['fingerprint']).get()
    except ValueError:
        last_tx = None

    __dict = {}
    __dict.update(ucoin.settings)
    __dict['version'] = 1
    __dict['number'] = 0 if not last_tx else last_tx['transaction']['number']+1
    __dict['previousHash'] = hashlib.sha1(("%(raw)s%(signature)s" % last_tx).encode('ascii')).hexdigest().upper()
    __dict['type'] = 'TRANSFER'

    # pprint(__dict)

    tx = """\
Version: %(version)d
Currency: %(currency)s
Sender: %(fingerprint)s
Number: %(number)d
""" % __dict

    if last_tx: tx += "PreviousHash: %(previousHash)s\n" % __dict

    tx += """\
Recipient: %(recipient)s
Type: %(type)s
Coins:
""" % __dict

    for coin in ucoin.settings['coins'].split(','):
        data = coin.split(':')
        issuer = data[0]
        for number in data[1:]:
            __dict.update(ucoin.hdc.coins.View(issuer, int(number)).get())
            tx += '%(id)s, %(transaction)s\n' % __dict

    tx += """\
Comment:
%(message)s
""" % __dict

    tx = tx.replace("\n", "\r\n")
    txs = ucoin.settings['gpg'].sign(tx, detach=True, keyid=ucoin.settings['user'])

    try:
        ucoin.hdc.transactions.Process().post(transaction=tx, signature=txs)
    except ValueError as e:
        print(e)
    else:
        print('Posted transfer transaction')

def fusion():
    logger.debug('fusion')

    if not ucoin.settings['coins']: ucoin.settings['coins'] = input()

    logger.debug('coins: %s' % ucoin.settings['coins'])

    try:
        last_tx = ucoin.hdc.transactions.sender.Last(ucoin.settings['fingerprint']).get()
    except ValueError:
        last_tx = None

    try:
        last_issuance = ucoin.hdc.transactions.sender.issuance.Last(ucoin.settings['fingerprint']).get()
    except ValueError:
        last_issuance = None

    __dict = {}
    __dict.update(ucoin.settings)
    __dict['version'] = 1
    __dict['number'] = 0 if not last_tx else last_tx['transaction']['number']+1
    __dict['previousHash'] = hashlib.sha1(("%(raw)s%(signature)s" % last_tx).encode('ascii')).hexdigest().upper()
    __dict['type'] = 'FUSION'

    # pprint(__dict)

    tx = """\
Version: %(version)d
Currency: %(currency)s
Sender: %(fingerprint)s
Number: %(number)d
""" % __dict

    if last_tx: tx += "PreviousHash: %(previousHash)s\n" % __dict

    tx += """\
Recipient: %(fingerprint)s
Type: %(type)s
Coins:
""" % __dict

    coins = []
    for coin in ucoin.settings['coins'].split(','):
        data = coin.split(':')
        issuer = data[0]
        for number in data[1:]:
            coins.append(ucoin.hdc.coins.View(issuer, int(number)).get())

    __sum = 0
    for coin in coins:
        base, power = coin['id'].split('-')[2:4]
        __sum += int(base) * 10**int(power)

    m = re.match(r'^(\d)(0*)$', str(__sum))

    if not m:
        print('bad sum value %d' % __sum)
        return

    def get_next_coin_number(coins):
        number = 0
        for c in coins:
            candidate = int(c['id'].split('-')[1])
            if candidate > number: number = candidate
        return number+1

    __dict['idx'] = 0 if not last_issuance else get_next_coin_number(last_issuance['transaction']['coins'])

    __dict['base'], __dict['power'] = int(m.groups()[0]), len(m.groups()[1])
    tx += '%(fingerprint)s-%(idx)d-%(base)d-%(power)d-F-%(number)d\n' % __dict

    for coin in coins:
        __dict.update(coin)
        tx += '%(id)s, %(transaction)s\n' % __dict

    tx += """\
Comment:
%(message)s
""" % __dict

    tx = tx.replace("\n", "\r\n")
    txs = ucoin.settings['gpg'].sign(tx, detach=True, keyid=ucoin.settings['user'])

    try:
        ucoin.hdc.transactions.Process().post(transaction=tx, signature=txs)
    except ValueError as e:
        print(e)
    else:
        print('Posted fusion transaction')

def host_add():
    logger.debug('host_add')

def host_rm():
    logger.debug('host_rm')

def host_list():
    logger.debug('host_list')

def trust_add():
    logger.debug('trust_add')

def trust_rm():
    logger.debug('trust_rm')

def trust_list():
    logger.debug('trust_list')

def tht():
    logger.debug('tht')

def pub_tht():
    logger.debug('pub_tht')

def forge_am():
    logger.debug('forge_am')

def clist():
    logger.debug('clist')

def cget():
    logger.debug('cget')

def send_pubkey():
    logger.debug('send_pubkey')

    data = None

    if ucoin.settings['user']:
        pass
    elif ucoin.settings['file']:
        data = open(ucoin.settings['file']).read()
    else:
        data = input()

def vote():
    logger.debug('vote')

    data = None

    if ucoin.settings['file']:
        data = open(ucoin.settings['file']).read()
    else:
        data = input()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='uCoin client.', formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    levels = OrderedDict([('debug', logging.DEBUG),
                          ('info', logging.INFO),
                          ('warning', logging.WARNING),
                          ('error', logging.ERROR),
                          ('quiet', logging.CRITICAL),])

    parser.add_argument('--verbose', '-v', choices=[x for x in levels.keys()], default='error', help='set a verbosity level')
    parser.add_argument('--levels', '-l', action='store_true', default=False, help='list all the verbosity levels')
    parser.add_argument('--output', '-o', help='all the logging messages are redirected to the specified filename.')
    parser.add_argument('--debug', '-d', action='store_const', const='debug', dest='verbose', help='Display all the messages.')
    parser.add_argument('--info', '-i', action='store_const', const='info', dest='verbose', help='Display the info messages.')
    parser.add_argument('--warning', '-w', action='store_const', const='warning', dest='verbose', help='Only display the warning and error messages.')
    parser.add_argument('--error', '-e', action='store_const', const='error', dest='verbose', help='Only display the error messages')
    parser.add_argument('--quiet', '-q', action='store_const', const='quiet', dest='verbose', help='Quiet level of verbosity only displaying the critical error messages.')

    parser.add_argument('--user', '-u', help='PGP key to use for signature')
    parser.add_argument('--server', '-s', help='uCoin server to look data in', default='localhost')
    parser.add_argument('--port', '-p', help='uCoin server port', type=int, default=8081)

    parser.add_argument('--config', '-c', help='set a config file', default='config.json')

    subparsers = parser.add_subparsers(help='sub-command help')

    subparsers.add_parser('current', help='Show current amendment of the contract').set_defaults(func=current)
    subparsers.add_parser('contract', help='List all amendments constituting the contract').set_defaults(func=contract)

    sp = subparsers.add_parser('lookup', help='Search for a public key')
    sp.add_argument('search', help='A value for searching in PGP certificates database. May start with \'0x\' for direct search on PGP fingerprint.')
    sp.set_defaults(func=lookup)

    subparsers.add_parser('peering', help='Show peering informations').set_defaults(func=peering)
    subparsers.add_parser('pubkey', help='Show pubkey of remote node').set_defaults(func=pubkey)
    subparsers.add_parser('index', help='List reiceved votes count for each amendment').set_defaults(func=index)

    sp = subparsers.add_parser('issue', help='Issue new coins')
    sp.add_argument('amendment', type=int, help='amendment number')
    sp.add_argument('coins', nargs='+', help='coins will respect this format [coin_value,number_of_zero_behind]')
    sp.add_argument('--message', '-m', help='write a comment', default='')
    sp.set_defaults(func=issue)

    sp = subparsers.add_parser('transfer', help='Transfers property of coins (coins a read from STDIN)')
    sp.add_argument('recipient', help='recipient address')
    sp.add_argument('coins', nargs='?', help='coins to send [coin,...]. If no value has passed, it will be read from STDIN.')
    sp.add_argument('--message', '-m', help='write a comment', default='')
    sp.set_defaults(func=transfer)

    sp = subparsers.add_parser('fusion', help='Fusion coins to make a bigger coin (coins a read from STDIN)')
    sp.add_argument('coins', nargs='?', help='coins to fusion [coin,...]. If no value has passed, it will be read from STDIN.')
    sp.add_argument('--message', '-m', help='write a comment', default='')
    sp.set_defaults(func=fusion)

    sp = subparsers.add_parser('host-add', help='Add given key fingerprint to hosts managing transactions of key -u')
    sp.add_argument('key', help='key fingerprint')
    sp.set_defaults(func=host_add)

    sp = subparsers.add_parser('host-rm', help='Same as \'host-add\', but remove host instead')
    sp.add_argument('key', help='key fingerprint')
    sp.set_defaults(func=host_rm)

    subparsers.add_parser('host-list', help='Show the list of keys').set_defaults(func=host_list)

    sp = subparsers.add_parser('trust-add', help='Add given key fingerprint to hosts key -u trust for receiving transactions')
    sp.add_argument('key', help='key fingerprint')
    sp.set_defaults(func=trust_add)

    sp = subparsers.add_parser('trust-rm', help='Same as \'trust-add\', but remove host instead')
    sp.add_argument('key', help='key fingerprint')
    sp.set_defaults(func=trust_rm)

    subparsers.add_parser('trust-list', help='Show the list of keys').set_defaults(func=trust_list)
    subparsers.add_parser('tht', help='Show THT entry resulting of host-* and trust-* commands').set_defaults(func=tht)
    subparsers.add_parser('pub-tht', help='Publish THT entry according to data returned by \'trust-list\' and \'host-list\'').set_defaults(func=pub_tht)

    sp = subparsers.add_parser('forge-am', help='Forge an amendment, following currently promoted of given node.')
    sp.add_argument('--dividend', '-d', help='Universal Dividend value')
    sp.add_argument('--power10', '-m', help='Minimal coin 10 power')
    sp.add_argument('--votes', '-n', help='Number of required votes', required=True)
    sp.add_argument('--timestamp', '-t', help='Generation timestamp')
    sp.set_defaults(func=forge_am)

    sp = subparsers.add_parser('clist', help='List coins of given user. May be limited by upper amount.')
    sp.add_argument('limit', nargs='?', help='limit value')
    sp.set_defaults(func=clist)

    sp = subparsers.add_parser('cget', help='Get coins for given values in user account.')
    sp.add_argument('value', nargs='+', help='value of the coin you want to select')
    sp.set_defaults(func=cget)

    sp = subparsers.add_parser('send-pubkey', help='Send signed public key [file] to a uCoin server. If -u option is provided, [file] is ommited. If [file] is not provided, it is read from STDIN. Note: [file] may be forged using \'forge-*\' commands.')
    sp.add_argument('file', nargs='?', help='signed public key to send')
    sp.set_defaults(func=send_pubkey)

    sp = subparsers.add_parser('vote', help='Signs given amendment [file] and sends it to a uCoin server. If [file] is not provided, it is read from STDIN.')
    sp.add_argument('file', nargs='?', help='amendment file')
    sp.set_defaults(func=vote)

    args = parser.parse_args()

    if args.levels:
        print("Here's the verbose levels available:")
        for keys in levels.keys():
            print("\t", keys)
        sys.exit()

    if (args.output):
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
            filename=args.output, filemode='a'
            )
    else:
        logging.basicConfig(
            level=levels.get(args.verbose, logging.NOTSET),
            format='%(name)-12s: %(levelname)-8s %(message)s'
        )

    ucoin.settings.update(args.__dict__)

    try:
        with open(args.config) as f:
            ucoin.settings.update(json.load(f))
    except FileNotFoundError:
        pass

    if ucoin.settings.get('user'):
        logger.debug('selected keyid: %s' % ucoin.settings['user'])
        ucoin.settings['gpg'] = gpg = gnupg.GPG(options=['-u %s' % ucoin.settings['user']])

        keys = gpg.list_keys(True)
        for idx, fp in enumerate(keys.fingerprints):
            if fp[-8:] == ucoin.settings['user']:
                ucoin.settings.update(keys[idx])
                break
    else:
        ucoin.settings['gpg'] = gpg = gnupg.GPG()

    ucoin.settings.update(ucoin.ucg.Peering().get())

    logger.debug(args)
    logger.debug(ucoin.settings)

    if 'func' not in args:
        parser.print_help()
        sys.exit()

    args.func()
