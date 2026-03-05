"""SQLAdmin configuration."""
from __future__ import annotations

from fastapi import FastAPI
from sqladmin import Admin, ModelView

from app.db import engine
from app.models import Comment, Post, User


class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.email, User.username, User.created_at]
    column_searchable_list = [User.email, User.username]
    column_sortable_list = [User.created_at]


class PostAdmin(ModelView, model=Post):
    column_list = [Post.id, Post.created_at, Post.type, Post.title, Post.author_id]
    column_searchable_list = [Post.title, Post.body]
    column_sortable_list = [Post.created_at]


class CommentAdmin(ModelView, model=Comment):
    column_list = [Comment.id, Comment.post_id, Comment.created_at, Comment.author_id]
    column_searchable_list = [Comment.body]
    column_sortable_list = [Comment.created_at]


def setup_admin(app: FastAPI) -> Admin:
    admin = Admin(app, engine)
    admin.add_view(UserAdmin)
    admin.add_view(PostAdmin)
    admin.add_view(CommentAdmin)
    return admin
