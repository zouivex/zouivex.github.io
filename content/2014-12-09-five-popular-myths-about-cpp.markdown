Title: 5个著名的关于C++的传说
Slug: five-popular-myths-about-cpp
Date: 2014-12-09 21:17:18
Modified: 2014-12-09 21:17:18
Category: 译文
Tags: cpp

# Introduction

In this three-part series, I will explore, and debunk, five popular myths about C++:

* “To understand C++, you must first learn C”
* “C++ is an Object-Oriented Language”
* “For reliable software, you need Garbage Collection”
* “For efficiency, you must write low-level code”
* “C++ is for large, complicated, programs only”

If you believe in any of these myths, or have colleagues who perpetuate them, this short article is for you. Several of these myths have been true for someone, for some task, at some time. However, with today’s C++, using widely available up-to date ISO C++ 2011 compilers, and tools, they are mere myths.

I deem these myths “popular” because I hear them often. Occasionally, they are supported by reasons, but more often they are simply stated as obvious, needing no support. Sometimes, they are used to dismiss C++ from consideration for some use.

Each myth requires a long paper or even a book to completely debunk, but my aim here is simply to raise the issues and to briefly state my reasons.

# Myth 1: “To understand C++, you must first learn C”

No. Learning basic programming using C++ is far easier than with C.

C is almost a subset of C++, but it is not the best subset to learn first because C lacks the notational support, the type safety, and the easier-to-use standard library offered by C++ to simplify simple tasks. Consider a trivial function to compose an email address:

```
string compose(const string& name, const string& domain)
{
  return name+'@'+domain;
}
```

It can be used like this

string addr = compose("gre","research.att.com");
The C version requires explicit manipulation of characters and explicit memory management:

```
char* compose(const char* name, const char* domain)
{
  char* res = malloc(strlen(name)+strlen(domain)+2); // space for strings, '@', and 0
  char* p = strcpy(res,name);
  p += strlen(name);
  *p = '@';
  strcpy(p+1,domain);
  return res;
}
```

It can be used like this

```
char* addr = compose("gre","research.att.com");
// …
free(addr); // release memory when done
```

Which version would you rather teach? Which version is easier to use? Did I really get the C version right? Are you sure? Why?

Finally, which version is likely to be the most efficient? Yes, the C++ version, because it does not have to count the argument characters and does not use the free store (dynamic memory) for short argument strings.

## Learning C++

This is not an odd isolated example. I consider it typical. So why do so many teachers insist on the “C first” approach?

Because that’s what they have done for ages.
Because that’s what the curriculum requires.
Because that’s the way the teachers learned it in their youth.
Because C is smaller than C++ it is assumed to be simpler to use.
Because the students have to learn C (or the C subset of C++) sooner or later anyway.
However, C is not the easiest or most useful subset of C++ to learn first. Furthermore, once you know a reasonable amount of C++, the C subset is easily learned. Learning C before C++ implies suffering errors that are easily avoided in C++ and learning techniques for mitigating them.

For a modern approach to teaching C++, see my Programming: Principles and Practice Using C++ [13]. It even has a chapter at the end showing how to use C. It has been used, reasonably successfully, with tens of thousands of beginning students in several universities. Its second edition uses C++11 and C++14 facilities to ease learning.

With C++11 [11-12], C++ has become more approachable for novices. For example, here is standard-library vector initialized with a sequence of elements:

```
vector<int> v = {1,2,3,5,8,13};
```

In C++98, we could only initialize arrays with lists. In C++11, we can define a constructor to accept a {} initializer list for any type for which we want one.

We could traverse that vector with a range-for loop:

```
for(int x : v) test(x);
```

This will call test() once for each element of v.

A range-for loop can traverse any sequence, so we could have simplified that example by using the initializer list directly:

```
for (int x : {1,2,3,5,8,13}) test(x);
```

One of the aims of C++11 was to make simple things simple. Naturally, this is done without adding performance penalties.

# Myth 2: “C++ is an Object-Oriented Language”

No. C++ supports OOP and other programming styles, but is deliberately not limited to any narrow view of “Object Oriented.” It supports a synthesis of programming techniques including object-oriented and generic programming. More often than not, the best solution to a problem involves more than one style (“paradigm”). By “best,” I mean shortest, most comprehensible, most efficient, most maintainable, etc.

The “C++ is an OOPL” myth leads people to consider C++ unnecessary (when compared to C) unless you need large class hierarchies with many virtual (run-time polymorphic) functions – and for many people and for many problems, such use is inappropriate. Believing this myth leads others to condemn C++ for not being purely OO; after all, if you equate “good” and “object-oriented,” C++ obviously contains much that is not OO and must therefore be deemed “not good.” In either case, this myth provides a good excuse for not learning C++.

Consider an example:

```
void rotate_and_draw(vector<Shape*>& vs, int r)
{
  for_each(vs.begin(),vs.end(), [](Shape* p) { p->rotate(r); });  // rotate all elements of vs
  for (Shape* p : vs) p->draw();                                  // draw all elements of vs
}
```

Is this object-oriented? Of course it is; it relies critically on a class hierarchy with virtual functions. It is generic? Of course it is; it relies critically on a parameterized container (vector) and the generic function for_each. Is this functional? Sort of; it uses a lambda (the [] construct). So what is it?  It is modern C++: C++11.

I used both the range-for loop and the standard-library algorithm for_each just to show off features. In real code, I would have use only one loop, which I could have written either way.

## Generic Programming

Would you like this code more generic? After all, it works only for vectors of pointers to Shapes. How about lists and built-in arrays? What about “smart pointers” (resource-management pointers), such as shared_ptr and unique_ptr? What about objects that are not called Shape that you can draw() and rotate()? Consider:

```
template<typename Iter>
void rotate_and_draw(Iter first, Iter last, int r)
{
  for_each(first,last,[](auto p) { p->rotate(r); });  // rotate all elements of [first:last)
  for (auto p = first; p!=last; ++p) p->draw();       // draw all elements of [first:last)
}
```

This works for any sequence you can iterate through from first to last. That’s the style of the C++ standard-library algorithms. I used auto to avoid having to name the type of the interface to “shape-like objects.” That’s a C++11 feature meaning “use the type of the expression used as initializer,” so for the for-loop p’s type is deduced to be whatever type first is. The use of auto to denote the argument type of a lambda is a C++14 feature, but already in use.

Consider:

```
void user(list<unique_ptr<Shape>>& lus, Container<Blob>& vb)
{
rotate_and_draw(lst.begin(),lst.end());
rotate_and_draw(begin(vb),end(vb));
}
```

Here, I assume that Blob is some graphical type with operations draw() and rotate() and that Container is some container type. The standard-library list (std::list) has member functions begin() and end() to help the user traverse its sequence of elements. That’s nice and classical OOP. But what if Container is something that does not support the C++ standard library’s notion of iterating over a half-open sequence, [b:e)? Something that does not have begin() and end() members? Well, I have never seen something container-like, that I couldn’t traverse, so we can define free-standing begin() and end() with appropriate semantics. The standard library provides that for C-style arrays, so if Container is a C-style array, the problem is solved – and C-style arrays are still very common.

## Adaptation

Consider a harder case: What if Container holds pointers to objects and has a different model for access and traversal? For example, assume that you are supposed to access a Container like this

```
for (auto p = c.first(); p!=nullptr; p=c.next()) { /* do something with *p */}
```

This style is not uncommon. We can map it to a [b:e) sequence like this

```
template<typename T> struct Iter {
  T* current;
  Container<T>& c;
};

template<typename T> Iter<T> begin(Container<T>& c) { return Iter<T>{c.first(),c}; }
template<typename T> Iter<T> end(Container<T>& c)   { return Iter<T>{nullptr}; }
template<typename T> Iter<T> operator++(Iter<T> p)  { p.current = c.next(); return this; }
template<typename T> T*      operator*(Iter<T> p)   { return p.current; }
```

Note that this is modification is nonintrusive: I did not have to make changes to Container or some Container class hierarchy to map Container into the model of traversal supported by the C++ standard library. It is a form of adaptation, rather than a form of refactoring.

I chose this example to show that these generic programming techniques are not restricted to the standard library (in which they are pervasive). Also, for most common definitions of “object oriented,” they are not object-oriented.

The idea that C++ code must be object-oriented (meaning use hierarchies and virtual functions everywhere) can be seriously damaging to performance. That view of OOP is great if you need run-time resolution of a set of types. I use it often for that. However, it is relatively rigid (not every related type fits into a hierarchy) and a virtual function call inhibits inlining (and that can cost you a factor of 50 in speed in simple and important cases).
