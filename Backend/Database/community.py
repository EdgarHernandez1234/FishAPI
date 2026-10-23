import time
import uuid

from bson import ObjectId
from bson.errors import InvalidId
from pymongo import ReturnDocument

from Database.db import posts


def _clean(post: dict) -> dict:
    """Swap MongoDB's ObjectId `_id` for a plain string `id` so FastAPI can turn it into JSON."""
    post["id"] = str(post.pop("_id"))
    return post


def _oid(post_id: str):
    """Turn id text from a URL into an ObjectId, or None if the text isn't a valid id."""
    try:
        return ObjectId(post_id)
    except (InvalidId, TypeError):
        return None

def create_post(data: dict) -> dict:
    doc = {
        **data,
        "createdAt": int(time.time() * 1000),   # milliseconds, like JavaScript's Date.now()
        "upvotes": 0,
        "downvotes": 0,
        "comments": [],
    }
    posts.insert_one(doc)                       # also adds the new "_id" to doc
    return _clean(doc)

def list_posts(limit: int = 200) -> list[dict]:
    return [_clean(p) for p in posts.find().sort("createdAt", -1).limit(limit)]

def add_comment(post_id: str, data: dict) -> dict | None:
    oid = _oid(post_id)
    if oid is None:
        return None
    
    comment = {"id": str(uuid.uuid4()), **data, "createdAt": int(time.time() * 1000)}
    result = posts.update_one({"_id": oid}, {"$push": {"comments": comment}})
    return comment if result.matched_count else None

def vote(post_id: str, direction: int, previous: int) -> dict | None:
    oid = _oid(post_id)
    if oid is None:
        return None

    change = {"upvotes": 0, "downvotes": 0}
    if previous == 1:
        change["upvotes"] -= 1          # undo the old upvote
    if previous == -1:
        change["downvotes"] -= 1        # undo the old downvote

    new_vote = 0 if previous == direction else direction   # clicking the same arrow again toggles it off
    if new_vote == 1:
        change["upvotes"] += 1
    if new_vote == -1:
        change["downvotes"] += 1

    post = posts.find_one_and_update(
        {"_id": oid}, {"$inc": change}, return_document=ReturnDocument.AFTER
    )
    if post is None:
        return None
    return {"upvotes": post["upvotes"], "downvotes": post["downvotes"], "vote": new_vote}