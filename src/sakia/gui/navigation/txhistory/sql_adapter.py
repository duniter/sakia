import math
import attr


TX_HISTORY_REQUEST = """
SELECT 
      transactions.ts,
      transactions.pubkey,
      total_amount((amount * -1), amountbase) as amount,
      transactions.comment ,
      transactions.sha_hash,
      transactions.written_on,
      transactions.txid
    FROM 
      transactions
    WHERE 
      transactions.currency = ? 
      and transactions.pubkey = ? 
      AND transactions.ts >= ? 
      and transactions.ts <= ? 
      AND transactions.issuers LIKE "%{pubkey}%"
      
UNION ALL
SELECT 
      transactions.ts,
      transactions.pubkey,
      total_amount(amount, amountbase) as amount,
      transactions.comment ,
      transactions.sha_hash,
      transactions.written_on,
      transactions.txid
    FROM 
      transactions
    WHERE 
      transactions.currency = ? 
      and transactions.pubkey = ? 
      AND transactions.ts >= ? 
      and transactions.ts <= ? 
      AND (transactions.receivers LIKE "%{pubkey}%"
        OR transactions.sha_hash = ?)
UNION ALL
SELECT 
      dividends.timestamp as ts,
      dividends.pubkey ,
      total_amount(amount, base) as amount,
      NULL as comment,
      NULL as sha_hash,
      dividends.block_number AS written_on,
      0 as txid
    FROM 
      dividends
    WHERE 
      dividends.currency = ? 
      and dividends.pubkey =? 
      AND dividends.timestamp >= ? 
      and dividends.timestamp <= ?
"""

PAGE_LENGTH = 50


@attr.s(frozen=True)
class TxHistorySqlAdapter:
    _conn = attr.ib()  # :type sqlite3.Connection

    def _transfers_and_dividends(self, currency, pubkey, ts_from, ts_to, stopline_hash, offset=0, limit=1000,
                                    sort_by="currency", sort_order="ASC"):
        """
        Get all transfers in the database on a given currency from or to a pubkey

        :param str pubkey: the criterions of the lookup
        :rtype: List[sakia.data.entities.Transaction]
        """
        request = (TX_HISTORY_REQUEST + """
ORDER BY {sort_by} {sort_order}, txid {sort_order}
LIMIT {limit} OFFSET {offset}""").format(offset=offset,
                                         limit=limit,
                                         sort_by=sort_by,
                                         sort_order=sort_order,
                                         pubkey=pubkey
                                         )
        c = self._conn.execute(request, (currency, pubkey, ts_from, ts_to,
                                         currency, pubkey, ts_from, ts_to, stopline_hash,
                                         currency, pubkey, ts_from, ts_to))
        datas = c.fetchall()
        if datas:
            return datas
        return []

    def _transfers_and_dividends_count(self, currency, pubkey, ts_from, ts_to, stopline_hash):
        """
        Get all transfers in the database on a given currency from or to a pubkey

        :param str pubkey: the criterions of the lookup
        :rtype: List[sakia.data.entities.Transaction]
        """
        request = ("""
SELECT COUNT(*)
FROM (
""" + TX_HISTORY_REQUEST + ")").format(pubkey=pubkey)
        c = self._conn.execute(request, (currency, pubkey, ts_from, ts_to,
                                                    currency, pubkey, ts_from, ts_to, stopline_hash,
                                                    currency, pubkey, ts_from, ts_to))
        datas = c.fetchone()
        if datas:
            return datas[0]
        return 0

    def transfers_and_dividends(self, currency, pubkey, page, ts_from, ts_to, stopline_hash, sort_by, sort_order):
        """
        Get all transfers and dividends from or to a given pubkey
        :param str currency:
        :param str pubkey:
        :param int page:
        :param int ts_from:
        :param int ts_to:
        :return: the list of Transaction entities
        :rtype: List[sakia.data.entities.Transaction]
        """
        return self._transfers_and_dividends(currency, pubkey, ts_from, ts_to, stopline_hash,
                                                      offset=page*PAGE_LENGTH,
                                                      limit=PAGE_LENGTH,
                                                      sort_by=sort_by, sort_order=sort_order)

    def pages(self, currency, pubkey, ts_from, ts_to, stopline_hash):
        """
        Get all transfers and dividends from or to a given pubkey
        :param str currency:
        :param str pubkey:
        :param int page:
        :param int ts_from:
        :param int ts_to:
        :return: the list of Transaction entities
        :rtype: List[sakia.data.entities.Transaction]
        """
        count = self._transfers_and_dividends_count(currency, pubkey, ts_from, ts_to, stopline_hash)
        return int(count / PAGE_LENGTH)


