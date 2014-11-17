Title: C++右值引用剖析
Slug: cpp-rvalue-references-explained
Date: 2014-11-15 15:03:14
Modified: 2014-11-15 15:03:14
Category: 译文
Tags: cpp

[TOC]

# 引言

右值引用是C++标准中新加入的功能。右值引用有点难以理解，初次接触的时候有点让人摸不清它的目的是什么、用来解决什么问题。因此本文不会直接介绍右值引用，而是先介绍它用来解决什么问题，然后展示右值引用如何解决问题。这样，关于右值引用的定义就更容易理解、更加自然。

右值引用至少要解决两个问题：

* 实现移动语义
* 完美传递

如果你对这两个问题还不了解，没有关系，本文接下来将详细介绍之。让我们先来介绍移动语义。但是正式开始之前，我们先来重温一下在C++中左值和右值都是什么。要想给出一个严格的定义还真不是那么容易，但是下面的解释对于本文应该足够了。

早期C语言中关于左值和右值的原始定义是这样的：左值就是可能出现在赋值语句左边或者右边的表达式，而右值就是只能出现在赋值语句右边的表达式。例如：

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

对于C++而言，这仍然是对于左值和右值的第一感的直觉的定义。然而，C++中用户自定义的类型引入了一些对象修改和赋值方面的问题，导致（C语言中的定义）在C++中是不正确的。关于这个问题我们没有必要继续深入探讨。有另外一种定义能够帮助我们理解右值引用（虽然这个定义仍然有疑议）：左值指向一块内存，并允许我们通过&操作符取其地址；而右值就是除了左值之外的表达式。例如：

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

如果你对于左值和右值的严格定义感兴趣，Mikael Kilpeläinen在ACCU中关于这个主题的[文章](http://accu.org/index.php/journals/227)非常适合入门。

# 移动语义

假设类X持有指向某资源的指针或handle，即m_pResource。我们说的资源指的是任何构造、复制、销毁需要耗费相当资源的对象。例如`std::vector`，它管理的对象存储于内存数组中。从逻辑上讲，类X的拷贝赋值操作符的实现如下：

``` C++
X& X::operator=(X const & rhs)
{
  // [...]
  // Destruct the resource that m_pResource refers to. 
  // Make a clone of what rhs.m_pResource refers to, and 
  // attach it to m_pResource.
  // [...]
}
```

同样，拷贝构造函数的实现也类似。我们假设X被这样调用：

``` C++
X foo();
X x;
// perhaps use x in various ways
x = foo();
```

上面最后一行代码：

* 释放x中持有的资源
* 从foo函数返回的临时对象中复制资源到x中
* 销毁临时对象，同时释放临时对象中的资源

很明显，直接交换x对象和临时对象中指向资源的指针或handle，然后在临时对象的析构函数中释放原始的资源，是可行的，也更有效率。换句话说，在赋值语句右手边是一个右值的情况下，我们希望拷贝赋值运算符有如下的行为：

``` C++
// [...]
// swap m_pResource and rhs.m_pResource
// [...]  
```

这就是移动语义。在C++11中，这种行为可以通过重载函数来实现：

``` C++
X& X::operator=(<mystery type> rhs)
{
  // [...]
  // swap this->m_pResource and rhs.m_pResource
  // [...]  
}
```

由于我们重载了拷贝赋值运算符，上面的“神秘类型”必须至少是一种引用类型：因为我们明确要求赋值语句右手边传入一个引用。此外，我们还期望“神秘类型”有这样的行为：当对普通引用类型和“神秘类型”进行重载时，如果参数是右值则重载到此“神秘类型”，如果参数是左值则重载到普通引用类型。

现在可以将上面的“神秘类型”替换为“右值引用”了，这就是右值引用的定义。

# 右值引用

假设X为任意类型，那么X&&就称为X类型的右值引用。为了与右值引用区分开，我们称普通的引用类型X&为左值引用。

右值引用类型与左值引用类型的行为类似，但是不完全一样。最重要的区别是在函数重载解析时，左值参数绑定为左值引用类型，而右值参数绑定为右值引用类型：

``` C++
void foo(X& x); // lvalue reference overload
void foo(X&& x); // rvalue reference overload

X x;
X foobar();

foo(x); // argument is lvalue: calls foo(X&)
foo(foobar()); // argument is rvalue: calls foo(X&&)
```
 
要点是：通过右值引用可以在编译期根据传入的参数是左值还是右值对函数进行选择（通过函数重载）。

如上面的例子所述，采用这种方法可以重载任何函数。但是大部分情况下，右值引用主要用在拷贝构造函数和拷贝赋值运算符中以实现移动语义：

``` C++
X& X::operator=(X const & rhs); // classical implementation
X& X::operator=(X&& rhs)
{
  // Move semantics: exchange content between this and rhs
  return *this;
}
```

在拷贝构造函数中使用右值引用进行重载的方法类似。

说明：C++中司空见惯的情况是，很多东西一眼看上去很正确但是或多或少不够完美。在某些情况下，如果简单地在拷贝构造函数中交换this和rhs中的内容还不够完美。我们将在第4节“强制移动语义”中继续讨论这个问题。

如果实现了：

``` C++
void foo(X&);
```

而没有实现：

``` C++
void foo(X&&);
```

那么行为并没有修改：foo可以传入左值参数，但是不能传入右值参数。而如果实现了：

``` C++
void foo(X const &);
```

而没有实现：

``` C++
void foo(X&&);
```

同样，行为依然没有修改：foo可以传入左值和右值参数，但是不能进一步区分参数是左值还是右值。只有同时实现下面的函数，才能区分左值和右值：

``` C++
void foo(X&&);
```

最后，如果你实现了：

``` C++
void foo(X&&);
```

但是没有实现：

``` C++
void foo(X&);
```

和

``` C++
void foo(X const &);
```

那么，根据C++11标准，foo可以传入右值参数，但是如果传入左值参数的话，将会导致编译错误。