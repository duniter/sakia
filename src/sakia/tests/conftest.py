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
from sakia.services import DocumentsService


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
                              NodesRepo(con), SourcesRepo(con), DividendsRepo(con))
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
def application(event_loop, meta_repo, sakia_options, app_data, user_parameters):
    app = Application(qapp=get_application(),
                       loop=event_loop,
                       options=sakia_options,
                       app_data=app_data,
                       parameters=user_parameters,
                       db=meta_repo)
    app.documents_service = DocumentsService.instanciate(app)
    return app


@pytest.fixture
def fake_server(event_loop):
    return event_loop.run_until_complete(mirage.Node.start(None, "test_currency", "12356", "123456", event_loop))


@pytest.fixture
def alice():
    return mirage.User.create("test_currency", "alice", "alicesalt", "alicepassword", BlockUID.empty())


@pytest.fixture
def bob():
    return mirage.User.create("test_currency", "bob", "bobsalt", "bobpassword", BlockUID.empty())


@pytest.fixture
def wrong_bob_uid():
    return mirage.User.create("test_currency", "wrong_bob", "bobsalt", "bobpassword", BlockUID.empty())


@pytest.fixture
def wrong_bob_pubkey():
    return mirage.User.create("test_currency", "bob", "wrongbobsalt", "bobpassword", BlockUID.empty())


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
    for i in range(0, 10):
        new_user = mirage.User.create("test_currency", "user{0}".format(i),
                                       "salt{0}".format(i), "password{0}".format(i),
                                      fake_server.forge.blocks[-1].blockUID)
        fake_server.forge.push(new_user.identity())
        fake_server.forge.push(new_user.join(fake_server.forge.blocks[-1].blockUID))
        fake_server.forge.forge_block()
        fake_server.forge.set_member(new_user.key.pubkey, True)
        fake_server.forge.generate_dividend()
        fake_server.forge.forge_block()
    return fake_server


@pytest.fixture
def application_with_one_connection(application, simple_fake_server, bob):
    current_block = simple_fake_server.forge.blocks[-1]
    last_ud_block = [b for b in simple_fake_server.forge.blocks if b.ud][-1]
    previous_ud_block = [b for b in simple_fake_server.forge.blocks if b.ud][-2]
    origin_block = simple_fake_server.forge.blocks[0]
    connection = Connection(currency="test_currency",
                      pubkey=bob.key.pubkey,
                      salt=bob.salt, uid=bob.uid,
                      scrypt_N=4096, scrypt_r=4, scrypt_p=2,
                      blockstamp=bob.blockstamp)
    application.db.connections_repo.insert(connection)
    blockchain_parameters = BlockchainParameters(*origin_block.parameters)
    blockchain = Blockchain(parameters=blockchain_parameters,
                            current_buid=current_block.blockUID,
                            current_members_count=current_block.members_count,
                            current_mass=simple_fake_server.forge.monetary_mass(current_block.number),
                            median_time=current_block.mediantime,
                            last_members_count=previous_ud_block.members_count,
                            last_ud=last_ud_block.ud,
                            last_ud_base=last_ud_block.unit_base,
                            last_ud_time=last_ud_block.mediantime,
                            previous_mass=simple_fake_server.forge.monetary_mass(previous_ud_block.number),
                            previous_members_count=previous_ud_block.members_count,
                            previous_ud=previous_ud_block.ud,
                            previous_ud_base=previous_ud_block.unit_base,
                            previous_ud_time=previous_ud_block.mediantime,
                            currency=simple_fake_server.forge.currency)
    application.db.blockchains_repo.insert(blockchain)
    for s in simple_fake_server.forge.user_identities[bob.key.pubkey].sources:
        application.db.sources_repo.insert(Source(currency=simple_fake_server.forge.currency,
                                                  pubkey=bob.key.pubkey,
                                                  identifier=s.origin_id,
                                                  noffset=s.index,
                                                  type=s.source,
                                                  amount=s.amount,
                                                  base=s.base))
    bob_blockstamp = simple_fake_server.forge.user_identities[bob.key.pubkey].blockstamp
    bob_user_identity = simple_fake_server.forge.user_identities[bob.key.pubkey]
    bob_ms = bob_user_identity.memberships[-1]
    bob_identity = Identity(currency=simple_fake_server.forge.currency,
                            pubkey=bob.key.pubkey,
                            uid=bob.uid,
                            blockstamp=bob_blockstamp,
                            signature=bob_user_identity.signature,
                            timestamp=simple_fake_server.forge.blocks[bob_blockstamp.number].mediantime,
                            written_on=0,
                            revoked_on=0,
                            member=bob_user_identity.member,
                            membership_buid=bob_ms.blockstamp,
                            membership_timestamp=simple_fake_server.forge.blocks[bob_ms.blockstamp.number].mediantime,
                            membership_type=bob_ms.type,
                            membership_written_on=simple_fake_server.forge.blocks[bob_ms.written_on].number)
    application.db.identities_repo.insert(bob_identity)
    application.instanciate_services()
    application.db.nodes_repo.insert(Node(currency=simple_fake_server.forge.currency,
                                          pubkey=simple_fake_server.forge.key.pubkey,
                                          endpoints=simple_fake_server.peer_doc().endpoints,
                                          peer_blockstamp=simple_fake_server.peer_doc().blockUID,
                                          uid="",
                                          current_buid=BlockUID(current_block.number, current_block.sha_hash),
                                          current_ts=current_block.mediantime,
                                          state=Node.ONLINE,
                                          software="duniter",
                                          version="0.40.2"))
    application.switch_language()

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

