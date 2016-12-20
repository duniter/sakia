import pytest
import asyncio
import quamash
import sqlite3
import mirage
from duniterpy.documents import BlockUID
from sakia.app import Application
from sakia.options import SakiaOptions
from sakia.data.files import AppDataFile
from sakia.data.entities import *
from sakia.data.repositories import *


_application_ = []


@pytest.yield_fixture
def event_loop():
    qapplication = get_application()
    loop = quamash.QSelectorEventLoop(qapplication)
    exceptions = []
    loop.set_exception_handler(lambda l, c: unitttest_exception_handler(exceptions, l, c))
    yield loop
    try:
        loop.close()
    finally:
        asyncio.set_event_loop(None)

    for exc in exceptions:
        raise exc


@pytest.fixture
def meta_repo():
    sqlite3.register_adapter(BlockUID, str)
    sqlite3.register_adapter(bool, int)
    sqlite3.register_converter("BOOLEAN", lambda v: bool(int(v)))
    con = sqlite3.connect(":memory:", detect_types=sqlite3.PARSE_DECLTYPES)
    meta_repo = SakiaDatabase(con,
                              ConnectionsRepo(con), IdentitiesRepo(con),
                              BlockchainsRepo(con), CertificationsRepo(con), TransactionsRepo(con),
                              NodesRepo(con), SourcesRepo(con))
    meta_repo.prepare()
    meta_repo.upgrade_database()
    return meta_repo


@pytest.fixture
def sakia_options(tmpdir):
    return SakiaOptions(tmpdir.dirname)


@pytest.fixture
def app_data(sakia_options):
    return AppDataFile.in_config_path(sakia_options.config_path).load_or_init()


@pytest.fixture
def user_parameters():
    return UserParameters()

@pytest.fixture
def connection(bob):
    return Connection(currency="testcurrency",
                      pubkey=bob.key.pubkey,
                      salt=bob.salt, uid=bob.uid,
                      scrypt_N=4096, scrypt_r=4, scrypt_p=2,
                      blockstamp=bob.blockstamp,
                      password="bobpassword")

@pytest.fixture
def application(event_loop, meta_repo, sakia_options, app_data, user_parameters):
    return Application(get_application(), event_loop, sakia_options, app_data, user_parameters, meta_repo, {}, {}, {}, {}, {})


@pytest.fixture
def fake_server(event_loop):
    return event_loop.run_until_complete(mirage.Node.start(None, "testcurrency", "12356", "123456", event_loop))


@pytest.fixture
def alice():
    return mirage.User.create("testcurrency", "alice", "alicesalt", "alicepassword", BlockUID.empty())


@pytest.fixture
def bob():
    return mirage.User.create("testcurrency", "bob", "bobsalt", "bobpassword", BlockUID.empty())


@pytest.fixture
def simple_fake_server(fake_server, alice, bob):
    fake_server.forge.push(alice.identity())
    fake_server.forge.push(bob.identity())
    fake_server.forge.push(alice.join(BlockUID.empty()))
    fake_server.forge.push(bob.join(BlockUID.empty()))
    fake_server.forge.push(alice.certify(bob, BlockUID.empty()))
    fake_server.forge.push(bob.certify(alice, BlockUID.empty()))
    fake_server.forge.forge_block()
    fake_server.forge.set_member(alice.key.pubkey, True)
    fake_server.forge.set_member(bob.key.pubkey, True)
    fake_server.forge.forge_block()
    fake_server.forge.forge_block()
    return fake_server


@pytest.fixture
def application_with_one_connection(application, connection, simple_fake_server):
    application.db.connections_repo.insert(connection)
    application.instanciate_services()
    application.db.nodes_repo.insert(Node(currency=simple_fake_server.forge.currency,
                                          pubkey=simple_fake_server.forge.key.pubkey,
                                          endpoints=simple_fake_server.peer_doc().endpoints,
                                          peer_blockstamp=simple_fake_server.peer_doc().blockstamp,
                                          uid=simple_fake_server.peer_doc.uid,
                                          current_buid=BlockUID(simple_fake_server.current_block(None)["number"],
                                                                simple_fake_server.current_block(None)["hash"]),
                                          current_ts=simple_fake_server.current_block(None)["medianTime"],
                                          state=Node.ONLINE,
                                          software="duniter",
                                          version="0.40.2"))
    return application


def unitttest_exception_handler(exceptions, loop, context):
    """
    An exception handler which exists the program if the exception
    was not catch
    :param loop: the asyncio loop
    :param context: the exception context
    """
    if 'exception' in context:
        exception = context['exception']
    else:
        exception = BaseException(context['message'])
    exceptions.append(exception)


def get_application():
    """Get the singleton QApplication"""
    from quamash import QApplication
    if not len(_application_):
        application = QApplication.instance()
        if not application:
            import sys
            application = QApplication(sys.argv)
        application.setQuitOnLastWindowClosed(False)
        _application_.append(application)
    return _application_[0]

