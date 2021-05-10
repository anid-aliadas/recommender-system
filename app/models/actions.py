from datetime import datetime
from typing import Tuple
from odmantic import Model
from enum import Enum

class ActionTypeProduct(str, Enum):
    VISIT = "visit"
    BUY = "buy"
    SEARCH = "search"

class ActionTypeVendor(str, Enum):
    VISIT = "visit"
    SEARCH = "search"

class ActionOverProduct(Model):
    user_id: str
    product_id: int
    type: ActionTypeProduct
    taxon_ids: Tuple[int, ...]
    created_at: datetime = datetime.now()

class ActionOverVendor(Model):
    user_id: str
    vendor_id: int
    type: ActionTypeVendor
    created_at: datetime = datetime.now()

class ActionOverQuery(Model):
    query_text: str
    results_id: Tuple[int, ...]
    searched_at: datetime = datetime.now()