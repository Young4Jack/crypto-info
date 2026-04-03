# backend/app/schemas/sorting.py (新建或加在现有的 schemas 文件中)
from pydantic import BaseModel
from typing import List

class SortItem(BaseModel):
    id: int
    sort_order: int

class SortUpdateRequest(BaseModel):
    items: List[SortItem]