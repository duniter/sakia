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

from parser import Parser
from pprint import pprint
import ucoin

URL = 'http://mycurrency.candan.fr:8081'
AUTH = False

def action_peering():
    pprint(ucoin.ucg.Peering().get())

def action_amendments():
    for am in ucoin.hdc.amendments.List().get():
        print(am['number'])

def action_transactions():
    for tx in ucoin.hdc.transactions.All().get():
        print(tx['hash'])

if __name__ == '__main__':
    parser = Parser(description='ucoin client.', verbose='error')

    parser.add_argument('--peering', '-p', help='get peering',
                        action='store_const', dest='action', const=action_peering)

    parser.add_argument('--amendments', '-a', help='get amendments list',
                        action='store_const', dest='action', const=action_amendments)

    parser.add_argument('--transactions', '-t', help='get transactions list',
                        action='store_const', dest='action', const=action_transactions)

    args = parser()

    if args.action: args.action()
