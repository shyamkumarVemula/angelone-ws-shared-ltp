import datetime

def weekly_expiry(day=3):  # Thursday
    today = datetime.date.today()
    expiry = today + datetime.timedelta((day - today.weekday()) % 7)
    return expiry.strftime("%d%b%y").upper()

from datetime import datetime
def get_nifty_strikes_for_expiry(allinst, expiry):
    strikes = set()

    for inst in allinst:
        if is_nifty_option(inst) and inst["expiry"] == expiry:
            strikes.add(parse_strike(inst))

    return sorted(strikes)
def get_current_nifty_expiry(allinst):
    expiries = get_nifty_expiries(allinst)
    return expiries[0] if expiries else None

def get_nifty_strikes_for_expiry(allinst, expiry):
    strikes = set()

    for inst in allinst:
        if is_nifty_option(inst) and inst["expiry"] == expiry:
            strikes.add(parse_strike(inst))

    return sorted(strikes)
def find_atm_strike(strikes, spot):
    return min(strikes, key=lambda x: abs(x - spot))
def get_option_symbol(allinst, expiry, strike, opt_type):
    target = f"NIFTY{expiry[:2]}{expiry[2:5]}{expiry[-2:]}{strike}{opt_type}"

    for inst in allinst:
        if inst["symbol"] == target:
            return f"NFO:{inst['symbol']}", inst["token"]

    return None, None

from datetime import datetime
def is_nifty_option(inst):
    return (
        inst.get("exch_seg") == "NFO"
        and inst.get("instrumenttype") == "OPTIDX"
        and inst.get("name") == "NIFTY"
    )
def parse_strike(inst):
    """
    Angel stores strike as price * 100
    """
    return int(float(inst["strike"]) / 100)

def get_nifty_expiries(allinst):
    expiries = set()

    for inst in allinst:
        if is_nifty_option(inst):
            expiries.add(inst["expiry"])

    return sorted(
        expiries,
        key=lambda x: datetime.strptime(x, "%d%b%Y")
    )
