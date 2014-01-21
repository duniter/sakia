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
import ucoin, json, logging, argparse, sys, gnupg, hashlib, re, datetime as dt
from collections import OrderedDict
from merkle import Merkle
from flask import Flask, request, render_template, jsonify
from io import StringIO
from werkzeug.contrib.cache import SimpleCache
from itertools import combinations, chain

logger = logging.getLogger("cli")
app = Flask(__name__)
cache = SimpleCache()

@app.template_filter('split')
def split_filter(s, sep=' '):
    return s.split(sep)

@app.template_filter('compute_coin')
def compute_coin_filter(coin):
    fpr, number, base, power, origin, origin_number = coin.split('-')
    return int(base)*10**int(power)

def render_prettyprint(template_name, result):
    s = StringIO()
    pprint(result, s)
    s = s.getvalue().replace('\\r', '').replace('\\n', '\n')
    return render_template(template_name, result=s, style='prettyprint')

def format_amendment(am):
    res = """\
Version\t\t\t%(version)s
Currency\t\t%(currency)s
Number\t\t\t%(number)s
GeneratedOn\t\t%(generated)s
UniversalDividend\t%(dividend)s
NextRequiredVotes\t%(nextVotes)s
PreviousHash\t\t%(previousHash)s
MembersRoot\t\t%(membersRoot)s
MembersCount\t\t%(membersCount)s
""" % am

    if am['membersChanges']:
        res += 'MembersChanges\n'
        for x in am['membersChanges']: res += '%s\n' % x

    res += """\
VotersRoot\t\t%(votersRoot)s
VotersCount\t\t%(votersCount)s
""" % am

    if am['votersChanges']:
        res += 'VotersChanges\n'
        for x in am['votersChanges']: res += '%s\n' % x

    return res

@app.route('/')
@app.route('/wallets')
def wallets():
    return render_template('wallets/index.html', settings=ucoin.settings)

@app.route('/wallets/new')
def new_wallet():
    return render_template('wallets/new.html', settings=ucoin.settings)

@app.route('/wallets/new/create')
def new_wallet_create():
    __input = 'Key-Type: %(type)s\nName-Email: %(email)s\nName-Real: %(realm)s\nKey-Length: %(length)s\n%%commit\n' % request.args
    newkey = ucoin.settings['gpg'].gen_key(__input)
    return jsonify(result="Your new key (%s) has been successfully created." % newkey.fingerprint)

def get_sender_transactions(pgp_fingerprint):
    k = 'sender_transactions_%s' % pgp_fingerprint
    rv = cache.get(k)
    if rv is None:
        rv = list(ucoin.hdc.transactions.Sender(pgp_fingerprint).get())
        cache.set(k, rv, timeout=5*60)
    return rv

def get_recipient_transactions(pgp_fingerprint):
    k = 'recipient_transactions_%s' % pgp_fingerprint
    rv = cache.get(k)
    if rv is None:
        rv = list(ucoin.hdc.transactions.Recipient(pgp_fingerprint).get())
        cache.set(k, rv, timeout=5*60)
    return rv

def clist(pgp_fingerprint):
    __list = ucoin.hdc.coins.List(pgp_fingerprint).get()
    coins = []
    __sum = 0
    for c in __list['coins']:
        for id in c['ids']:
            n,b,p,t,i = id.split('-')
            amount = int(b) * 10**int(p)
            __dict = {'issuer': c['issuer'], 'number': int(n), 'base': int(b), 'power': int(p), 'type': t, 'type_number': int(i), 'amount': amount}
            coins.append(__dict)
            __sum += amount
    return __sum, coins

@app.route('/wallets/<pgp_fingerprint>/history')
@app.route('/wallets/<pgp_fingerprint>/history/<type>')
def wallet_history(pgp_fingerprint, type='all'):
    sender = get_sender_transactions(pgp_fingerprint)
    recipient = get_recipient_transactions(pgp_fingerprint)

    return render_template('wallets/history.html',
                           settings=ucoin.settings,
                           key=ucoin.settings['secret_keys'].get(pgp_fingerprint),
                           sender=sender,
                           recipient=recipient,
                           type=type,
                           clist=clist(pgp_fingerprint))

def powerset(iterable):
  xs = list(iterable)
  return chain.from_iterable( combinations(xs,n) for n in range(len(xs)+1) )

def cget(pgp_fingerprint, values):
    __list = ucoin.hdc.coins.List(pgp_fingerprint).get()
    coins = {}
    for c in __list['coins']:
        for id in c['ids']:
            n,b,p,t,i = id.split('-')
            amount = int(b) * 10**int(p)
            coins[amount] = {'issuer': c['issuer'], 'number': int(n), 'base': int(b), 'power': int(p), 'type': t, 'type_number': int(i), 'amount': amount}

    issuers = {}
    for v in values:
        if v in coins:
            c = coins[v]
            issuers[c['issuer']] = issuers.get(c['issuer']) or []
            issuers[c['issuer']].append(c)
        else:
            raise ValueError('You do not have enough coins of value (%d)' % v)

    res = ''
    for i, issuer in enumerate(issuers):
        if i > 0: res += ','
        res += issuer
        for c in issuers[issuer]:
            res += ':%(number)d' % c

    return res

def transfer(pgp_fingerprint, recipient, coins, message=''):
    try:
        last_tx = ucoin.hdc.transactions.sender.Last(pgp_fingerprint).get()
    except ValueError:
        last_tx = None

    __dict = {}
    __dict.update(ucoin.settings)
    __dict['version'] = 1
    __dict['number'] = 0 if not last_tx else last_tx['transaction']['number']+1
    __dict['previousHash'] = hashlib.sha1(("%(raw)s%(signature)s" % last_tx).encode('ascii')).hexdigest().upper()
    __dict['type'] = 'TRANSFER'
    __dict['recipient'] = recipient
    __dict['message'] = message

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

    for coin in coins.split(','):
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
    txs = ucoin.settings['gpg'].sign(tx, detach=True)

    try:
        ucoin.hdc.transactions.Process().post(transaction=tx, signature=txs)
    except ValueError as e:
        print(e)
    else:
        return True

    return False

@app.route('/wallets/<pgp_fingerprint>/transfer', methods=['GET', 'POST',])
def wallet_transfer(pgp_fingerprint):
    balance, __clist = clist(pgp_fingerprint)
    amounts = [x['amount'] for x in __clist]
    __combinations = list(map(lambda x: (sum(x), x), powerset(amounts)))[1:]
    __combinations.sort()
    sums = [x[0] for x in __combinations]

    if request.method == 'GET':
        return render_template('wallets/transfer.html',
                               settings=ucoin.settings,
                               key=ucoin.settings['secret_keys'].get(pgp_fingerprint),
                               clist=(balance,__clist),
                               sums=sums)

    amount = request.form.get('amount', type=int)
    recipient = request.form.get('recipient')
    message = request.form.get('message', '')

    try:
        idx = sums.index(amount)
    except ValueError as e:
        raise ValueError(e)

    selected_combination = __combinations[idx][1]

    coins = cget(pgp_fingerprint, selected_combination)

    if not transfer(pgp_fingerprint, recipient, coins, message):
        raise ValueError('transfer error')

    return '%s %s' % (str(selected_combination), recipient)

@app.route('/wallets/public_keys')
def wallet_public_keys():
    keys = ucoin.settings['public_keys']
    for k,v in keys.items():
        v['value'] = v['fingerprint']
        v['tokens'] = v['uids']
        v['name'] = v['uids'][0]
    return json.dumps(list(keys.values()))

@app.route('/api')
def api():
    return render_template('api/index.html')

@app.route('/api/pks/add', methods=['GET', 'POST'])
def pks_add():
    if request.method == 'GET':
        return render_template('api/result.html', result='POST Method has to be used')

    keytext = request.form.get('keytext')
    keysign = request.form.get('keysign')

    return render_template('api/result.html', result=ucoin.pks.Add().post(keytext=keytext, keysign=keysign))

@app.route('/api/pks/lookup')
def pks_lookup():
    search = request.args.get('search', '')
    op = request.args.get('op', 'get')

    return render_template('api/result.html', result=ucoin.pks.Lookup().get(search=search, op=op))

@app.route('/api/pks/all')
def pks_all():
    return render_prettyprint('api/result.html', list(ucoin.pks.All().get()))

@app.route('/api/ucg/pubkey')
def ucg_pubkey():
    return render_template('api/result.html', result=ucoin.ucg.Pubkey().get(), style='text')

@app.route('/api/ucg/peering')
def ucg_peering():
    return render_prettyprint('api/result.html', ucoin.ucg.Peering().get())

@app.route('/api/ucg/peering/keys')
def ucg_peering_keys():
    return render_prettyprint('api/result.html', list(ucoin.ucg.peering.Keys().get()))

@app.route('/api/ucg/peering/peer')
def ucg_peering_peer():
    return render_prettyprint('api/result.html', ucoin.ucg.peering.Peer().get())

@app.route('/api/ucg/peering/peers', methods=['GET', 'POST'])
def ucg_peering_peers():
    if request.method == 'GET':
        return render_prettyprint('api/result.html', list(ucoin.ucg.peering.Peers().get()))

    entry = request.form.get('entry')
    signature = request.form.get('signature')

    return render_prettyprint('api/result.html', ucoin.ucg.peering.Peers().post(entry=entry, signature=signature))

@app.route('/api/ucg/peering/peers/upstream')
def ucg_peering_peers_upstream():
    return render_prettyprint('api/result.html', ucoin.ucg.peering.peers.UpStream().get())

@app.route('/api/ucg/peering/peers/upstream/<pgp_fingerprint>')
def ucg_peering_peers_upstream_pgp(pgp_fingerprint):
    return render_prettyprint('api/result.html', ucoin.ucg.peering.peers.UpStream(pgp_fingerprint).get())

@app.route('/api/ucg/peering/peers/downstream')
def ucg_peering_peers_downstream():
    return render_prettyprint('api/result.html', ucoin.ucg.peering.peers.DownStream().get())

@app.route('/api/ucg/peering/peers/downstream/<pgp_fingerprint>')
def ucg_peering_peers_downstream_pgp(pgp_fingerprint):
    return render_prettyprint('api/result.html', ucoin.ucg.peering.peers.DownStream(pgp_fingerprint).get())

@app.route('/api/ucg/peering/forward', methods=['GET', 'POST'])
def ucg_peering_forward():
    if request.method == 'GET':
        return render_template('api/result.html', result='POST Method has to be used')

    forward = request.form.get('forward')
    signature = request.form.get('signature')

    return render_prettyprint('api/result.html', ucoin.ucg.peering.Forward().post(forward=forward, signature=signature))

@app.route('/api/ucg/peering/status', methods=['GET', 'POST'])
def ucg_peering_status():
    if request.method == 'GET':
        return render_template('api/result.html', result='POST Method has to be used')

    status = request.form.get('status')
    signature = request.form.get('signature')

    return render_prettyprint('api/result.html', ucoin.ucg.peering.Status().post(status=status, signature=signature))

@app.route('/api/ucg/tht', methods=['GET', 'POST',])
def ucg_tht():
    if request.method == 'GET':
        return render_prettyprint('api/result.html', list(ucoin.ucg.THT().get()))

    entry = request.form.get('entry')
    signature = request.form.get('signature')

    return render_prettyprint('api/result.html', ucoin.ucg.THT().post(entry=entry, signature=signature))

@app.route('/api/ucg/tht/<pgp_fingerprint>')
def ucg_tht_pgp(pgp_fingerprint):
    return render_prettyprint('api/result.html', ucoin.ucg.THT(pgp_fingerprint).get())

@app.route('/api/hdc/amendments/current')
def hdc_amendments_current():
    return render_prettyprint('api/result.html', ucoin.hdc.amendments.Current().get())

@app.route('/api/hdc/amendments/current/votes')
def hdc_amendments_current_votes():
    return render_prettyprint('api/result.html', list(ucoin.hdc.amendments.CurrentVotes().get()))

@app.route('/api/hdc/amendments/promoted')
def hdc_amendments_promoted():
    return render_prettyprint('api/result.html', ucoin.hdc.amendments.Promoted().get())

@app.route('/api/hdc/amendments/promoted/<int:amendment_number>')
def hdc_amendments_promoted_am(amendment_number):
    return render_prettyprint('api/result.html', ucoin.hdc.amendments.Promoted(amendment_number).get())

@app.route('/api/hdc/amendments/view/<amendment_id>/members')
def hdc_amendments_view_am_members(amendment_id):
    return render_prettyprint('api/result.html', list(ucoin.hdc.amendments.views.Members(amendment_id).get()))

@app.route('/api/hdc/amendments/view/<amendment_id>/self')
def hdc_amendments_view_am_self(amendment_id):
    return render_prettyprint('api/result.html', ucoin.hdc.amendments.views.Self(amendment_id).get())

@app.route('/api/hdc/amendments/view/<amendment_id>/voters')
def hdc_amendments_view_am_voters(amendment_id):
    return render_prettyprint('api/result.html', list(ucoin.hdc.amendments.views.Voters(amendment_id).get()))

@app.route('/api/hdc/amendments/view/<amendment_id>/signatures')
def hdc_amendments_view_am_signatures(amendment_id):
    return render_prettyprint('api/result.html', list(ucoin.hdc.amendments.views.Signatures(amendment_id).get()))

@app.route('/api/hdc/amendments/votes', methods=['GET', 'POST'])
def hdc_amendments_votes():
    if request.method == 'GET':
        return render_prettyprint('api/result.html', ucoin.hdc.amendments.Votes().get())

    amendment = request.form.get('amendment')
    signature = request.form.get('signature')
    peer = request.form.get('peer')

    return render_prettyprint('api/result.html', ucoin.hdc.amendments.Votes().post(amendment=amendment, signature=signature, peer=peer))

@app.route('/api/hdc/amendments/votes/<amendment_id>')
def hdc_amendments_votes_am(amendment_id):
    return render_prettyprint('api/result.html', list(ucoin.hdc.amendments.Votes(amendment_id).get()))

@app.route('/api/hdc/coins/<pgp_fingerprint>/list')
def hdc_coins_pgp_list(pgp_fingerprint):
    return render_prettyprint('api/result.html', ucoin.hdc.coins.List(pgp_fingerprint).get())

@app.route('/api/hdc/coins/<pgp_fingerprint>/view/<int:coin_number>')
def hdc_coins_pgp_view_coin(pgp_fingerprint):
    return render_prettyprint('api/result.html', ucoin.hdc.coins.List(pgp_fingerprint, coin_number).get())

@app.route('/api/hdc/coins/<pgp_fingerprint>/view/<int:coin_number>/history')
def hdc_coins_pgp_view_coin_history(pgp_fingerprint):
    return render_prettyprint('api/result.html', ucoin.hdc.coins.view.History(pgp_fingerprint, coin_number).get())

@app.route('/api/hdc/transactions/process', methods=['POST',])
def hdc_transactions_process():
    transaction = request.form.get('transaction')
    signature = request.form.get('signature')

    return render_prettyprint('api/result.html', ucoin.hdc.transactions.Process().post(transaction=transaction, signature=signature))

@app.route('/api/hdc/transactions/all')
def hdc_transactions_all():
    return render_prettyprint('api/result.html', list(ucoin.hdc.transactions.All().get()))

@app.route('/api/hdc/transactions/keys')
def hdc_transactions_keys():
    return render_prettyprint('api/result.html', list(ucoin.hdc.transactions.Keys().get()))

@app.route('/api/hdc/transactions/last')
def hdc_transactions_last():
    return render_prettyprint('api/result.html', ucoin.hdc.transactions.Last().get())

@app.route('/api/hdc/transactions/last/<int:count>')
def hdc_transactions_last_count(count):
    return render_prettyprint('api/result.html', ucoin.hdc.transactions.Last(count).get())

@app.route('/api/hdc/transactions/sender/<pgp_fingerprint>')
def hdc_transactions_sender_pgp(pgp_fingerprint):
    return render_prettyprint('api/result.html', list(ucoin.hdc.transactions.Sender(pgp_fingerprint).get()))

@app.route('/api/hdc/transactions/sender/<pgp_fingerprint>/last')
def hdc_transactions_sender_pgp_last(pgp_fingerprint):
    return render_prettyprint('api/result.html', ucoin.hdc.transactions.sender.Last(pgp_fingerprint).get())

@app.route('/api/hdc/transactions/sender/<pgp_fingerprint>/last/<int:count>')
def hdc_transactions_sender_pgp_last_count(pgp_fingerprint, count):
    return render_prettyprint('api/result.html', ucoin.hdc.transactions.sender.Last(pgp_fingerprint, count).get())

@app.route('/api/hdc/transactions/sender/<pgp_fingerprint>/transfer')
def hdc_transactions_sender_pgp_transfer(pgp_fingerprint):
    return render_prettyprint('api/result.html', list(ucoin.hdc.transactions.sender.Transfer(pgp_fingerprint).get()))

@app.route('/api/hdc/transactions/sender/<pgp_fingerprint>/issuance')
def hdc_transactions_sender_pgp_issuance(pgp_fingerprint):
    return render_prettyprint('api/result.html', list(ucoin.hdc.transactions.sender.Issuance(pgp_fingerprint).get()))

@app.route('/api/hdc/transactions/sender/<pgp_fingerprint>/issuance/last')
def hdc_transactions_sender_pgp_issuance_last(pgp_fingerprint):
    return render_prettyprint('api/result.html', ucoin.hdc.transactions.sender.issuance.Last(pgp_fingerprint).get())

@app.route('/api/hdc/transactions/sender/<pgp_fingerprint>/issuance/fusion')
def hdc_transactions_sender_pgp_issuance_fusion(pgp_fingerprint):
    return render_prettyprint('api/result.html', list(ucoin.hdc.transactions.sender.issuance.Fusion(pgp_fingerprint).get()))

@app.route('/api/hdc/transactions/sender/<pgp_fingerprint>/issuance/dividend')
def hdc_transactions_sender_pgp_issuance_dividend(pgp_fingerprint):
    return render_prettyprint('api/result.html', list(ucoin.hdc.transactions.sender.issuance.Dividend(pgp_fingerprint).get()))

@app.route('/api/hdc/transactions/sender/<pgp_fingerprint>/issuance/dividend/<int:amendment_number>')
def hdc_transactions_sender_pgp_issuance_dividend_am(pgp_fingerprint, amendment_number):
    return render_prettyprint('api/result.html', list(ucoin.hdc.transactions.sender.issuance.Dividend(pgp_fingerprint, amendment_number).get()))

@app.route('/api/hdc/transactions/recipient/<pgp_fingerprint>')
def hdc_transactions_recipient_pgp(pgp_fingerprint):
    return render_prettyprint('api/result.html', list(ucoin.hdc.transactions.Recipient(pgp_fingerprint).get()))

@app.route('/api/hdc/transactions/view/<transaction_id>')
def hdc_transactions_view_tx(transaction_id):
    return render_prettyprint('api/result.html', ucoin.hdc.transactions.View(transaction_id).get())

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='uCoin webclient.', formatter_class=argparse.ArgumentDefaultsHelpFormatter)

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

    def run():
        print('Running...')
        app.run(debug=True)

    subparsers.add_parser('run', help='Run the webclient').set_defaults(func=run)

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

        secret_keys = gpg.list_keys(True)
        public_keys = gpg.list_keys()

        for idx, fp in enumerate(secret_keys.fingerprints):
            if fp[-8:] == ucoin.settings['user']:
                ucoin.settings.update(secret_keys[idx])
                break

        ucoin.settings['secret_keys'] = __secret_keys = {}
        ucoin.settings['public_keys'] = __public_keys = {}

        for k in secret_keys: __secret_keys[k['fingerprint']] = k
        for k in public_keys: __public_keys[k['fingerprint']] = k
    else:
        ucoin.settings['gpg'] = gpg = gnupg.GPG()

    ucoin.settings.update(ucoin.ucg.Peering().get())

    logger.debug(args)
    logger.debug(ucoin.settings)

    if 'func' not in args:
        parser.print_help()
        sys.exit()

    args.func()
