import attr

from ..entities import Contact


@attr.s(frozen=True)
class ContactsRepo:
    """
    The repository for Contacts entities.
    """
    _conn = attr.ib()  # :type sqlite3.Contact
    _primary_keys = (attr.fields(Contact).contact_id,)

    def insert(self, contact):
        """
        Commit a contact to the database
        :param sakia.data.entities.Contact contact: the contact to commit
        """
        contacts_list = attr.astuple(contact, tuple_factory=list)
        contacts_list[3] = "\n".join([str(n) for n in contacts_list[3]])
        if contacts_list[-1] == -1:
            col_names = ",".join([a.name for a in attr.fields(Contact)[:-1]])
            contacts_list = contacts_list[:-1]
        else:
            col_names = ",".join([a.name for a in attr.fields(Contact)])
        values = ",".join(['?'] * len(contacts_list))
        cursor = self._conn.cursor()
        cursor.execute("INSERT INTO contacts ({:}) VALUES ({:})".format(col_names, values), contacts_list)
        contact.contact_id = cursor.lastrowid


    def update(self, contact):
        """
        Update an existing contact in the database
        :param sakia.data.entities.Contact contact: the certification to update
        """
        updated_fields = attr.astuple(contact, tuple_factory=list,
                                      filter=attr.filters.exclude(*ContactsRepo._primary_keys))

        updated_fields[3] = "\n".join([str(n) for n in updated_fields[3]])

        where_fields = attr.astuple(contact, tuple_factory=list,
                                    filter=attr.filters.include(*ContactsRepo._primary_keys))

        self._conn.execute("""UPDATE contacts SET
                              currency=?,
                              name=?,
                              pubkey=?,
                              fields=?
                              WHERE
                              contact_id=?
                          """, updated_fields + where_fields)

    def get_one(self, **search):
        """
        Get an existing contact in the database
        :param dict search: the criterions of the lookup
        :rtype: sakia.data.entities.Contact
        """
        filters = []
        values = []
        for k, v in search.items():
            filters.append("{k}=?".format(k=k))
            values.append(v)

        request = "SELECT * FROM contacts WHERE {filters}".format(filters=" AND ".join(filters))

        c = self._conn.execute(request, tuple(values))
        data = c.fetchone()
        if data:
            return Contact(*data)

    def get_all(self, **search):
        """
        Get all existing contact in the database corresponding to the search
        :param dict search: the criterions of the lookup
        :rtype: sakia.data.entities.Contact
        """
        filters = []
        values = []
        for k, v in search.items():
            value = v
            filters.append("{contact} = ?".format(contact=k))
            values.append(value)

        request = "SELECT * FROM contacts"
        if filters:
            request += " WHERE {filters}".format(filters=" AND ".join(filters))

        c = self._conn.execute(request, tuple(values))
        datas = c.fetchall()
        if datas:
            return [Contact(*data) for data in datas]
        return []

    def drop(self, contact):
        """
        Drop an existing contact from the database
        :param sakia.data.entities.Contact contact: the contact to update
        """
        where_fields = attr.astuple(contact, filter=attr.filters.include(*ContactsRepo._primary_keys))
        self._conn.execute("""DELETE FROM contacts
                              WHERE
                              contact_id=?""", where_fields)
