Title: C++右值引用剖析
Slug: cpp-rvalue-references-explained
Date: 2014-11-15 15:03:14
Modified: 2014-11-15 15:03:14
Category: 译文
Tags: cpp

[TOC]

# 引言

右值引用是C++标准中新加入的功能。右值引用有点难以理解，初次接触的时候有点让人摸不清它的目的是什么、用来解决什么问题。因此我不会直接开始解释右值引用，而是先介绍它用来解决什么问题，然后展示右值引用如何解决问题。这样，关于右值引用的定义将会更加容易理解、更加自然。

右值引用至少要解决两个问题：

* 实现移动语义
* 完美传递

如果你对这两个问题还不了解，没有关系，本文接下来将详细介绍之。让我们先来介绍移动语义。但是正式开始之前，我们先来重温一下在C++中左值和右值都是什么。要想给出一个严格的定义还真不是那么容易，但是下面的解释对于本文应该足够了。

早期C语言中关于左值和右值的原始定义是这样的：左值就是可能出现在赋值语句左边或者右边的表达式，而右值就是只能出现在赋值语句右边的表达是。例如：

``` C++
int a = 42;
int b = 43;

// a and b are both l-values:
a = b; // ok
b = a; // ok
a = a * b; // ok

// a * b is an rvalue:
int c = a * b; // ok, rvalue on right hand side of assignment
a * b = 42; // error, rvalue on left hand side of assignment
```

对于C++而言，这仍然是对于左值和右值的非常有用的第一感、直觉的定义。然而，C++中的用户定义的类型，引入了一些修改和赋值方面的问题，导致（C语言中的定义）在C++中是不正确的。关于这个问题我们没有必要再继续深入探讨。有另外一种定义能够帮助我们理解右值引用（虽然这个定义也还有些疑议）：左值引用表达式指向一块内存，并允许我们通过&操作符取其地址；而右值就是除了左值之外的表达式。例如：

``` C++
// lvalues:
//
int i = 42;
i = 43; // ok, i is an lvalue
int* p = &i; // ok, i is an lvalue
int& foo();
foo() = 42; // ok, foo() is an lvalue
int* p1 = &foo(); // ok, foo() is an lvalue

// rvalues:
//
int foobar();
int j = 0;
j = foobar(); // ok, foobar() is an rvalue
int* p2 = &foobar(); // error, cannot take the address of an rvalue
j = 42; // ok, 42 is an rvalue
```

如果你对于左值和右值的严格定义感兴趣，Mikael Kilpeläinen在ACCU中关于这个主题的[文章](http://accu.org/index.php/journals/227)是非常好的入门文章。