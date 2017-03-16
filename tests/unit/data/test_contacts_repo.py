from sakia.data.repositories import ContactsRepo
from sakia.data.entities import Contact


def test_add_get_drop_contact(meta_repo):
    contacts_repo = ContactsRepo(meta_repo.conn)
    new_contact = Contact("testcurrency",
                          "john",
                          "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ")
    contacts_repo.insert(new_contact)
    contact = contacts_repo.get_one(currency="testcurrency",
                                    pubkey="7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
                                    name="john")
    assert contact.currency == "testcurrency"
    assert contact.pubkey == "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ"
    assert contact.name == "john"
#    assert contact.contact_id == new_contact.contact_id
    contacts_repo.drop(contact)
    meta_repo.conn.commit()
    contact = contacts_repo.get_one(currency="testcurrency",
                                    pubkey="7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
                                    name="john")
    assert contact is None
