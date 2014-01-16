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
import ucoin, json, logging, argparse, sys
from collections import OrderedDict

logger = logging.getLogger("cli")

# def action_transactions():
#     for tx in ucoin.hdc.transactions.All().get():
#         print(tx['hash'])

def print_amendment(am):
    print('Version\t\t\t',      am['version'])
    print('Currency\t\t',       am['currency'])
    print('Number\t\t\t',       am['number'])
    print('GeneratedOn\t\t',    am['generated'])
    print('UniversalDividend\t', am['dividend'])
    print('NextRequiredVotes\t', am['nextVotes'])
    print('PreviousHash\t\t',   am['previousHash'])
    print('MembersRoot\t\t',    am['membersRoot'])
    print('MembersCount\t\t',   am['membersCount'])
    if am['membersChanges']:
        print('MembersChanges')
        for x in am['membersChanges']: print(x)
    print('VotersRoot\t\t',     am['votersRoot'])
    print('VotersCount\t\t',    am['votersCount'])
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

    print('Currency\t',         peer['currency'])
    print('Public key FPR\t',   peer['key'])
    print('Contract\t',         peer['contract']['currentNumber'] + '-' + peer['contract']['hash'])
    print('Public keys\t',      peer['merkles']['pks/all']['leavesCount'])
    print('Remote host\t',      peer['remote']['host'])
    if peer['remote']['ipv4']:
        print('Remote ipv4\t',  peer['remote']['ipv4'])
    if peer['remote']['ipv6']:
        print('Remote ipv6\t',  peer['remote']['ipv6'])
    print('Remote port\t',      peer['remote']['port'])

def pubkey():
    logger.debug('pubkey')

    print(ucoin.ucg.Pubkey().get())

def index():
    logger.debug('index')

def issue():
    logger.debug('issue')

def transfer():
    logger.debug('transfer')
    coins = input('coins: ')
    logger.debug(coins)

def fusion():
    logger.debug('fusion')
    coins = input('coins: ')
    logger.debug(coins)

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
    parser = argparse.ArgumentParser(description='ucoin client.', formatter_class=argparse.ArgumentDefaultsHelpFormatter)

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

    parser_current = subparsers.add_parser('current', help='Show current amendment of the contract')
    parser_current.set_defaults(func=current)

    parser_contract = subparsers.add_parser('contract', help='List all amendments constituting the contract')
    parser_contract.set_defaults(func=contract)

    parser_lookup = subparsers.add_parser('lookup', help='Search for a public key')
    parser_lookup.add_argument('search', help='A value for searching in PGP certificates database. May start with \'0x\' for direct search on PGP fingerprint.')
    parser_lookup.set_defaults(func=lookup)

    parser_peering = subparsers.add_parser('peering', help='Show peering informations')
    parser_peering.set_defaults(func=peering)

    parser_pubkey = subparsers.add_parser('pubkey', help='Show pubkey of remote node')
    parser_pubkey.set_defaults(func=pubkey)

    parser_index = subparsers.add_parser('index', help='List reiceved votes count for each amendment')
    parser_index.set_defaults(func=index)

    parser_issue = subparsers.add_parser('issue', help='Issue new coins')
    parser_issue.add_argument('amendment', help='amendment number')
    parser_issue.add_argument('coins', help='coins')
    parser_issue.add_argument('comment', help='write a comment')
    parser_issue.set_defaults(func=issue)

    parser_transfer = subparsers.add_parser('transfer', help='Transfers property of coins (coins a read from STDIN)')
    parser_transfer.add_argument('recipient', help='recipient address')
    parser_transfer.add_argument('comment', help='write a comment')
    parser_transfer.set_defaults(func=transfer)

    parser_fusion = subparsers.add_parser('fusion', help='Fusion coins to make a bigger coin (coins a read from STDIN)')
    parser_fusion.add_argument('comment', help='write a comment')
    parser_fusion.set_defaults(func=fusion)

    parser_host_add = subparsers.add_parser('host-add', help='Add given key fingerprint to hosts managing transactions of key -u')
    parser_host_add.add_argument('key', help='key fingerprint')
    parser_host_add.set_defaults(func=host_add)

    parser_host_rm = subparsers.add_parser('host-rm', help='Same as \'host-add\', but remove host instead')
    parser_host_rm.add_argument('key', help='key fingerprint')
    parser_host_rm.set_defaults(func=host_rm)

    parser_host_list = subparsers.add_parser('host-list', help='Show the list of keys')
    parser_host_list.set_defaults(func=host_list)

    parser_trust_add = subparsers.add_parser('trust-add', help='Add given key fingerprint to hosts key -u trust for receiving transactions')
    parser_trust_add.add_argument('key', help='key fingerprint')
    parser_trust_add.set_defaults(func=trust_add)

    parser_trust_rm = subparsers.add_parser('trust-rm', help='Same as \'trust-add\', but remove host instead')
    parser_trust_rm.add_argument('key', help='key fingerprint')
    parser_trust_rm.set_defaults(func=trust_rm)

    parser_trust_list = subparsers.add_parser('trust-list', help='Show the list of keys')
    parser_trust_list.set_defaults(func=trust_list)

    parser_tht = subparsers.add_parser('tht', help='Show THT entry resulting of host-* and trust-* commands')
    parser_tht.set_defaults(func=tht)

    parser_pub_tht = subparsers.add_parser('pub-tht', help='Publish THT entry according to data returned by \'trust-list\' and \'host-list\'')
    parser_pub_tht.set_defaults(func=pub_tht)

    parser_forge_am = subparsers.add_parser('forge-am', help='Forge an amendment, following currently promoted of given node.')
    parser_forge_am.add_argument('--dividend', '-d', help='Universal Dividend value')
    parser_forge_am.add_argument('--power10', '-m', help='Minimal coin 10 power')
    parser_forge_am.add_argument('--votes', '-n', help='Number of required votes', required=True)
    parser_forge_am.add_argument('--timestamp', '-t', help='Generation timestamp')
    parser_forge_am.set_defaults(func=forge_am)

    parser_clist = subparsers.add_parser('clist', help='List coins of given user. May be limited by upper amount.')
    parser_clist.add_argument('limit', help='limit value')
    parser_clist.set_defaults(func=clist)

    parser_cget = subparsers.add_parser('cget', help='Get coins for given values in user account.')
    parser_cget.add_argument('value', nargs='+', help='value of the coin you want to select')
    parser_cget.set_defaults(func=cget)

    parser_send_pubkey = subparsers.add_parser('send-pubkey', help='Send signed public key [file] to a uCoin server. If -u option is provided, [file] is ommited. If [file] is not provided, it is read from STDIN. Note: [file] may be forged using \'forge-*\' commands.')
    parser_send_pubkey.add_argument('file', nargs='?', help='signed public key to send')
    parser_send_pubkey.set_defaults(func=send_pubkey)

    parser_vote = subparsers.add_parser('vote', help='Signs given amendment [file] and sends it to a uCoin server. If [file] is not provided, it is read from STDIN.')
    parser_vote.add_argument('file', nargs='?', help='amendment file')
    parser_vote.set_defaults(func=vote)

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

    logger.debug(args)
    logger.debug(ucoin.settings)

    if 'func' not in args:
        parser.print_help()
        sys.exit()

    args.func()
