from pydantic import BaseModel, Field
from typing import Literal

question_type = Literal["Questions", "Fishing Tips", "Locations", "Gear", "Catch Reports"]

class PostCreate(BaseModel):
    username: str = Field(min_length=1, max_length=40)
    title: str = Field(min_length=1, max_length= 40)
    question_type: str
    question_body: str = Field(min_length=1, max_length=3000)

class CommentCreate(BaseModel):
    author: str = Field(min_length=1, max_length=40)
    content: str = Field(min_length=1, max_length=1500)

class VoteRequest(BaseModel):
    direction: Literal[1, -1]
    previous: Literal[-1, 0, 1] = 0   # this browser's vote before the click