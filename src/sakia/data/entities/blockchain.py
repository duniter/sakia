import attr
from duniterpy.documents import block_uid, BlockUID


@attr.s(hash=False)
class BlockchainParameters:
    # The decimal percent growth of the UD every [dt] period
    c = attr.ib(convert=float, default=0, cmp=False, hash=False)
    # Time period between two UD in seconds
    dt = attr.ib(convert=int, default=0, cmp=False, hash=False)
    # UD(0), i.e. initial Universal Dividend
    ud0 = attr.ib(convert=int, default=0, cmp=False, hash=False)
    # Minimum delay between 2 certifications of a same issuer, in seconds. Must be positive or zero
    sig_period = attr.ib(convert=int, default=0, cmp=False, hash=False)
    # Maximum quantity of active certifications made by member
    sig_stock = attr.ib(convert=int, default=0, cmp=False, hash=False)
    # Maximum age of a active signature (in seconds)
    sig_validity = attr.ib(convert=int, default=0, cmp=False, hash=False)
    # Minimum quantity of signatures to be part of the WoT
    sig_qty = attr.ib(convert=int, default=0, cmp=False, hash=False)
    # Maximum delay in seconds a certification can wait before being expired for non-writing
    sig_window = attr.ib(convert=int, default=0, cmp=False, hash=False)
    # Maximum delay in seconds an identity can wait before being expired for non-writing
    idty_window = attr.ib(convert=int, default=0, cmp=False, hash=False)
    # Maximum delay in seconds a membership can wait before being expired for non-writing
    ms_window = attr.ib(convert=int, default=0, cmp=False, hash=False)
    # Minimum decimal percent of sentries to reach to match the distance rule
    xpercent = attr.ib(convert=float, default=0, cmp=False, hash=False)
    # Maximum age of an active membership( in seconds)
    ms_validity = attr.ib(convert=int, default=0, cmp=False, hash=False)
    # Maximum distance between each WoT member and a newcomer
    step_max = attr.ib(convert=int, default=0, cmp=False, hash=False)
    # Number of blocks used for calculating median time
    median_time_blocks = attr.ib(convert=int, default=0, cmp=False, hash=False)
    # The average time for writing 1 block (wished time) in seconds
    avg_gen_time = attr.ib(convert=int, default=0, cmp=False, hash=False)
    # The number of blocks required to evaluate again PoWMin value
    dt_diff_eval = attr.ib(convert=int, default=0, cmp=False, hash=False)
    # The decimal percent of previous issuers to reach for personalized difficulty
    percent_rot = attr.ib(convert=float, default=0, cmp=False, hash=False)
    # The first UD time
    ud_time_0 = attr.ib(convert=int, default=0, cmp=False, hash=False)
    # The first UD reavallued
    ud_reeval_time_0 = attr.ib(convert=int, default=0, cmp=False, hash=False)
    # The dt recomputation of the ud
    dt_reeval = attr.ib(convert=int, default=0, cmp=False, hash=False)


@attr.s(hash=True)
class Blockchain:
    # Parameters in block 0
    parameters = attr.ib(default=BlockchainParameters(), cmp=False, hash=False)
    # block number and hash
    current_buid = attr.ib(convert=block_uid, default=BlockUID.empty())
    # Number of members
    current_members_count = attr.ib(convert=int, default=0, cmp=False, hash=False)
    # Current monetary mass in units
    current_mass = attr.ib(convert=int, default=0, cmp=False, hash=False)
    # Median time in seconds
    median_time = attr.ib(convert=int, default=0, cmp=False, hash=False)
    # Last members count
    last_mass = attr.ib(convert=int, default=0, cmp=False, hash=False)
    # Last members count
    last_members_count = attr.ib(convert=int, default=0, cmp=False, hash=False)
    # Last UD amount in units (multiply by 10^base)
    last_ud = attr.ib(convert=int, default=1, cmp=False, hash=False)
    # Last UD base
    last_ud_base = attr.ib(convert=int, default=0, cmp=False, hash=False)
    # Last UD base
    last_ud_time = attr.ib(convert=int, default=0, cmp=False, hash=False)
    # Previous monetary mass in units
    previous_mass = attr.ib(convert=int, default=0, cmp=False, hash=False)
    # Previous members count
    previous_members_count = attr.ib(convert=int, default=0, cmp=False, hash=False)
    # Previous UD amount in units (multiply by 10^base)
    previous_ud = attr.ib(convert=int, default=0, cmp=False, hash=False)
    # Previous UD base
    previous_ud_base = attr.ib(convert=int, default=0, cmp=False, hash=False)
    # Previous UD base
    previous_ud_time = attr.ib(convert=int, default=0, cmp=False, hash=False)
    # Currency name
    currency = attr.ib(convert=str, default="", cmp=False, hash=False)
