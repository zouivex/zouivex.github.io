Title: GotW89 智能指针
Slug: smart-pointers
Date: 2014-10-30 21:22:04
Modified: 2014-10-30 21:22:04
Category: 译文
Tags: cpp
Status: draft

When should you use shared_ptr vs. unique_ptr?

When in doubt, prefer unique_ptr by default, and you can always later move-convert to shared_ptr if you need it. If you do know from the start you need shared ownership, however, go directly to shared_ptr via make_shared (see #2 below).

There are three major reasons to say “when in doubt, prefer unique_ptr.”

First, use the simplest semantics that are sufficient: Choose the right smart pointer to most directly express your intent, and what you need (now). If you are creating a new object and don’t know that you’ll eventually need shared ownership, use unique_ptr which expresses unique ownership. You can still put it in a container (e.g., vector<unique_ptr<widget>>) and do most other things you want to do with a raw pointer, only safely. If you later need shared ownership, you can always move-convert the unique_ptr to a shared_ptr.

Second, a unique_ptr is more efficient than a shared_ptr. A unique_ptr doesn’t need to maintain reference count information and a control block under the covers, and is designed to be just about as cheap to move and use as a raw pointer. When you don’t ask for more than you need, you don’t incur overheads you won’t use.

Third, starting with unique_ptr is more flexible and keeps your options open. If you start with a unique_ptr, you can always later convert to a shared_ptr via move, or to another custom smart pointer (or even to a raw pointer) via .get() or .release().

Guideline: Prefer to use the standard smart pointers, unique_ptr by default and shared_ptr if sharing is needed. They are the common types that all C++ libraries can understand. Use other smart pointer types only if necessary for interoperability with other libraries, or when necessary for custom behavior you can’t achieve with deleters and allocators on the standard pointers.

# 什么时候使用`shared_ptr`，什么时候`unique_ptr`？

如果拿不准该使用哪种智能指针，可以默认使用`unique_ptr`，将来确有需要时切换为使用`shared_ptr`。