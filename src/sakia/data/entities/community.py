import attr


@attr.s()
class Community:
    # The decimal percent growth of the UD every [dt] period
    c = attr.ib(convert=float, default=0, cmp=False)
    # Time period between two UD in seconds
    dt = attr.ib(convert=int, default=0, cmp=False)
    # UD(0), i.e. initial Universal Dividend
    ud0 = attr.ib(convert=int, default=0, cmp=False)
    # Minimum delay between 2 certifications of a same issuer, in seconds. Must be positive or zero
    sig_period = attr.ib(convert=int, default=0, cmp=False)
    # Maximum quantity of active certifications made by member
    sig_stock = attr.ib(convert=int, default=0, cmp=False)
    # Maximum delay in seconds a certification can wait before being expired for non-writing
    sig_window = attr.ib(convert=int, default=0, cmp=False)
    # Maximum age of a active signature (in seconds)
    sig_validity = attr.ib(convert=int, default=0, cmp=False)
    # Minimum quantity of signatures to be part of the WoT
    sig_qty = attr.ib(convert=int, default=0, cmp=False)
    # Minimum decimal percent of sentries to reach to match the distance rule
    xpercent = attr.ib(convert=float, default=0, cmp=False)
    # Maximum age of an active membership( in seconds)
    ms_validity = attr.ib(convert=int, default=0, cmp=False)
    # Maximum distance between each WoT member and a newcomer
    step_max = attr.ib(convert=int, default=0, cmp=False)
    # Number of blocks used for calculating median time
    median_time_blocks = attr.ib(convert=int, default=0, cmp=False)
    # The average time for writing 1 block (wished time) in seconds
    avg_gen_time = attr.ib(convert=int, default=0, cmp=False)
    # The number of blocks required to evaluate again PoWMin value
    dt_diff_eval = attr.ib(convert=int, default=0, cmp=False)
    # The number of previous blocks to check for personalized difficulty
    blocks_rot = attr.ib(convert=int, default=0, cmp=False)
    # The decimal percent of previous issuers to reach for personalized difficulty
    percent_rot = attr.ib(convert=float, default=0, cmp=False)
    # Currency name
    currency = attr.ib(convert=str, default="", cmp=False)



