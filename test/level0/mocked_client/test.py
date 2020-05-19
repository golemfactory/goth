from market import level0_market
from activity import level0_activity
from payment import level0_payment

agreement_id = level0_market()
level0_activity(agreement_id)
level0_payment(agreement_id)
