Title: C++右值引用剖析
Slug: cpp-rvalue-references-explained
Date: 2014-11-15 15:03:14
Modified: 2014-11-15 15:03:14
Category: 译文
Tags: cpp

[TOC]

# 引言

右值引用是C++标准中新加入的功能。它有点难以理解，初次接触的时候让人弄不清设计它的目的是什么、用来解决什么问题。因此本文不会直接介绍右值引用，而是先介绍它用来解决什么问题，然后展示右值引用如何解决问题。这样，关于右值引用的定义就更容易理解、更加自然。

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

对于C++而言，这仍然是对于左值和右值的第一感的直觉的定义。然而，C++的用户自定义类型引入了一些对象修改和赋值方面的问题，从而（C语言中的定义）在C++中就不正确了。关于这个问题我们没有必要继续深入探讨。有另外一种定义能够帮助我们理解右值引用（虽然这个定义仍然有疑议）：左值指向一块内存，并允许我们通过&操作符取其地址；而右值就是除了左值之外的其它表达式。例如：

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

如果你对左值和右值的严格定义感兴趣，Mikael Kilpeläinen在ACCU中关于这个主题的[文章](http://accu.org/index.php/journals/227)非常适合入门。

# 移动语义

假设类X持有指向某资源的指针或handle，名为m_pResource。我们所说的资源指的是任何构造、复制、销毁需要耗费相当系统资源的对象。例如`std::vector`，它管理的对象存储于内存数组中。从逻辑上讲，类X的拷贝赋值操作符的实现如下：

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

那么行为并没有改变：foo可以传入左值参数，但是不能传入右值参数。而如果实现了：

``` C++
void foo(X const &);
```

而没有实现：

``` C++
void foo(X&&);
```

同样，行为依然没有改变：foo可以传入左值和右值参数，但是不能进一步区分参数是左值还是右值。只有同时实现下面的函数，才能区分左值和右值：

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

# 强制移动语义

我们都知道，C++标准的“第一修正案”中规定：委员会不能以任何形式的规定阻止C++程序员搬起石头砸自己的脚。用稍微正式的话说，如果可以进行选择的话，C++语言倾向于提供给程序员更多的控制而不是对程序员的粗心错误进行保护。以此为指导思想，C++11中不光可以对右值使用移动语义，还允许对左值使用移动语义。标准库中的swap函数就是一个很好的例子。假设X是一个实现了拷贝构造函数和拷贝赋值运算符的类，通过这种方式对右值实现了移动语义。

``` C++
template<class T>
void swap(T& a, T& b) 
{ 
  T tmp(a);
  a = b; 
  b = tmp; 
} 

X a, b;
swap(a, b);
```

上面的例子中没有右值。因此，swap函数中的3行代码实际上都不是移动语义。但是我们很清楚什么时候可以安全地使用移动语义：当一个变量作为拷贝构造函数或者拷贝赋值操作符的参数时，此变量要么再也不会被使用了，要么只作为赋值操作的目标变量。

C++11中，库函数`std::move`可以在这个时候派上用场。此函数的唯一作用是将传入的参数转化为右值。从而在C++11中，标准库中的swap函数的具体实现如下：

``` C++
template<class T> 
void swap(T& a, T& b) 
{ 
  T tmp(std::move(a));
  a = std::move(b); 
  b = std::move(tmp);
} 

X a, b;
swap(a, b);
```

现在swap函数的所有代码都使用了移动语义。需要注意，对于那些没有实现移动语义的类型（即没有实现移动构造函数或者移动赋值操作符的类），上面的swap函数的行为与旧swap函数一样。

std::move函数的实现非常简单。但是遗憾的是，现在解释其具体实现还不是时候。本文将在后面对其进行详细解释。

在我们的代码中能够使用std::move时就尽量使用，有两个好处：

* 对于那些实现了移动语义的类型，标准库的许多算法会自动使用移动语义，从而有可能大幅度提升性能。原地排序算法就是一个很好的例子：在原地排序算法中大部分操作都是元素的移动操作，那么swap函数对于那些实现了移动语义的对象则进行移动操作。
* STL库经常要求某些特定对象是可复制的。例如，需要存入容器中的元素。进一步观察，我们发现大部分情况下，对象只需要可移动即可。因此，在C++11代码中之前需要对象可复制的场合，现在只需要对象可移动即可。例如，当将这些类型的对象作为容器的元素时。

既然我们理解了std::move，那么我们可以进一步讨论为什么对拷贝赋值运算符进行右值引用重载仍然有些问题。以下面变量的简单赋值操作为例：

``` C++
a = b; 
```

此时，你期望发生什么事情？你期望的是，将a对象替换为b对象的拷贝，同时，还期望释放之前的a对象。那么考虑下面这行代码：

``` C++
a = std::move(b); 
```

如果像上面的swap函数中那样实现了移动语义，那么上面这行代码的效果是a和b持有的对象进行了交换。此时a和b都还没有被销毁。a之前持有的对象最终会被释放，也就是当b对象离开作用域的时候。当然，如果又有其它的对象移动到b，那么之前a持有的对象继续被交换到其它对象。因此，对于拷贝赋值运算符来说，并不知道交换进来的对象将在什么时候销毁。

所以在某种程度上，我们慢慢地堕入了无法确定地销毁对象的无间道中：我们将对象赋值给某变量，但是该变量先前持有的对象却依然在某个地方逍遥法外。其实只要该对象的析构函数对于外部世界没有副作用，就不会有问题。例如在析构函数中释放锁就有问题。因此，只要对象的析构函数有副作用，那么就应该在右值引用所重载的拷贝赋值运算符函数中显式地执行。

``` C++
X& X::operator=(X&& rhs)
{

  // Perform a cleanup that takes care of at least those parts of the
  // destructor that have side effects. Be sure to leave the object
  // in a destructible and assignable state.

  // Move semantics: exchange content between this and rhs
  
  return *this;
}
```

# 那么右值引用本身是右值吗？

同样，假设类X重载了拷贝构造函数和拷贝赋值运算符，实现了移动语义。我们看下面的代码：

``` C++
void foo(X&& x)
{
  X anotherX = x;
  // ...
}
```

这里有一个非常有意思的问题：foo函数中的代码到底调用的是X的哪个构造函数？此处的变量x声明为右值引用，优先绑定到右值的引用类型。因此，我们可以合情合理地推论x应该像右值那样进行绑定，也就是调用下面这个函数：

``` C++
X(X&& rhs);
```

换句话说，我们以为声明为右值引用的变量本身也应该是右值。但是右值引用的设计者们选择更加巧妙的方案：即声明为右值引用的变量本身可以是左值也可以是右值。区分的标准是：如果变量有名字那么为左值，否则为右值。

上面例子中的x声明为右值引用，但是它有名字，因此它是一个左值：

``` C++
void foo(X&& x)
{
  X anotherX = x; // calls X(X const & rhs)
}
```

下面例子中的变量声明为右值引用，并且没有名字，因此是右值：

``` C++
X&& goo();
X x = goo(); // calls X(X&& rhs) because the thing on
             // the right hand side has no name
```

右值引用的设计的基于这样的考虑：如果允许对有名字的变量不声不响地使用移动语义的话，例如下面的代码：

``` C++
X anotherX = x;
// x is still in scope!
```

would be dangerously confusing and error-prone because the thing from which we just moved, that is, the thing that we just pilfered, is still accessible on subsequent lines of code. But the whole point of move semantics was to apply it only where it "doesn't matter," in the sense that the thing from which we move dies and goes away right after the moving. Hence the rule, "If it has a name, then it's an lvalue."

将使代码难以理解，并且非常容易出错，因为我们移动的对象，也就是刚被偷走的对象，在后面的代码中仍然可以访问到。But the whole point of move semantics was to apply it only where it "doesn't matter," in the sense that the thing from which we move dies and goes away right after the moving. 所以，规则就是，”如果有名字，那么就是左值”。

So then what about the other part, "If it does not have a name, then it's an rvalue?" Looking at the goo example above, it is technically possible, though not very likely, that the expression goo() in the second line of the example refers to something that is still accessible after it has been moved from. But recall from the previous section: sometimes that's what we want! We want to be able to force move semantics on lvalues at our discretion, and it is precisely the rule, "If it does not have a name, then it's an rvalue" that allows us to achieve that in a controlled manner. That's how the function std::move works. Although it is still too early to show you the exact implementation, we just got a step closer to understanding std::move. It passes its argument right through by reference, doing nothing with it at all, and its result type is rvalue reference. So the expression

``` C++
std::move(x)
```

is declared as an rvalue reference and does not have a name. Hence, it is an rvalue. Thus, std::move "turns its argument into an rvalue even if it isn't," and it achieves that by "hiding the name."

声明为右值引用，并且没有名字，所以是右值。也就是说，std::move将传入的参数转换为右值，实现方式就是“隐藏变量的名字”。

下面的代码展示了上面的区分左右值的规则的重要性。我们实现了类Base，并且通过重载Base的拷贝构造函数和拷贝赋值运算符的方式实现了移动语义：

``` C++
Base(Base const & rhs); // non-move semantics
Base(Base&& rhs); // move semantics
```

现在我们要从Base类派生出Derived类。为了确保对Derived类的对象的Base子对象执行移动语义，必须也重载Derived类的拷贝构造函数以及拷贝赋值运算符。让我们看看拷贝构造函数的具体实现，拷贝赋值运算符的实现方式相同。其左值的版本相当直接：

``` C++
Derived(Derived const & rhs) 
  : Base(rhs)
{
  // Derived-specific stuff
}
```

而右值版本则不那么简单直接了。如果我们没有弄明白上面提到的区分左右值的规则的话，我们可能这样实现：

``` C++
Derived(Derived&& rhs) 
  : Base(rhs) // wrong: rhs is an lvalue
{
  // Derived-specific stuff
}
```

此时，调用的是Base类的左值版本的拷贝构造函数，因为参数rhs有名字，所以它是一个左值。其实我们希望调用的是Base类的右值版本的拷贝构造函数，所以我们的实现代码应该这样写：

``` C++
Derived(Derived&& rhs) 
  : Base(std::move(rhs)) // good, calls Base(Base&& rhs)
{
  // Derived-specific stuff
}
```

# 移动语义和编译器优化

Consider the following function definition:

``` C++
X foo()
{
  X x;
  // perhaps do something to x
  return x;
}
```

Now suppose that as before, X is a class for which we have overloaded the copy constructor and copy assignment operator to implement move semantics. If you take the function definition above at face value, you may be tempted to say, wait a minute, there is a value copy happening here from x to the location of foo's return value. Let me make sure we're using move semantics instead:

``` C++
X foo()
{
  X x;
  // perhaps do something to x
  return std::move(x); // making it worse!
}
```

Unfortunately, that would make things worse rather than better. Any modern compiler will apply return value optimization to the original function definition. In other words, rather than constructing an X locally and then copying it out, the compiler would construct the X object directly at the location of foo's return value. Rather obviously, that's even better than move semantics.
So as you can see, in order to really use rvalue references and move semantics in an optimal way, you need to fully understand and take into account today's compilers' "special effects" such as return value optimization and copy elision. Dave Abrahams has written an excellent series of articles on this subject on his blog. The details get pretty subtle, but hey, we chose C++ as our language of choice for a reason, right? We made our beds, so now let's lie in them. 

# 完美传递：问题定义

The other problem besides move semantics that rvalue references were designed to solve is the perfect forwarding problem. Consider the following simple factory function:

``` C++
template<typename T, typename Arg> 
shared_ptr<T> factory(Arg arg)
{ 
  return shared_ptr<T>(new T(arg));
} 
```

Obviously, the intent here is to forward the argument arg from the factory function to T's constructor. Ideally, as far as arg is concerned, everything should behave just as if the factory function weren't there and the constructor were called directly in the client code: perfect forwarding. The code above fails miserably at that: it introduces an extra call by value, which is particularly bad if the constructor takes its argument by reference.

The most common solution, chosen e.g. by boost::bind, is to let the outer function take the argument by reference:

``` C++
template<typename T, typename Arg> 
shared_ptr<T> factory(Arg& arg)
{ 
  return shared_ptr<T>(new T(arg));
} 
```

That's better, but not perfect. The problem is that now, the factory function cannot be called on rvalues:

``` C++
factory<X>(hoo()); // error if hoo returns by value
factory<X>(41); // error
```

This can be fixed by providing an overload which takes its argument by const reference:

``` C++
template<typename T, typename Arg> 
shared_ptr<T> factory(Arg const & arg)
{ 
  return shared_ptr<T>(new T(arg));
} 
```

There are two problems with this approach. Firstly, if factory had not one, but several arguments, you would have to provide overloads for all combinations of non-const and const reference for the various arguments. Thus, the solution scales extremely poorly to functions with several arguments.

Secondly, this kind of forwarding is less than perfect because it blocks out move semantics: the argument of the constructor of T in the body of factory is an lvalue. Therefore, move semantics can never happen even if it would without the wrapping function.
It turns out that rvalue references can be used to solve both these problems. They make it possible to achieve truly perfect forwarding without the use of overloads. In order to understand how, we need to look at two more rules for rvalue references. 

# 完美传递：问题求解

The first of the remaining two rules for rvalue references affects old-style lvalue references as well. Recall that in pre-11 C++, it was not allowed to take a reference to a reference: something like A& & would cause a compile error. C++11, by contrast, introduces the following reference collapsing rules:

``` C++
A& & becomes A&
A& && becomes A&
A&& & becomes A&
A&& && becomes A&&
```

Secondly, there is a special template argument deduction rule for function templates that take an argument by rvalue reference to a template argument:

``` C++
template<typename T>
void foo(T&&);
```

Here, the following apply:

* When foo is called on an lvalue of type A, then T resolves to A& and hence, by the reference collapsing rules above, the argument type effectively becomes A&.
* When foo is called on an rvalue of type A, then T resolves to A, and hence the argument type becomes A&&. 

Given these rules, we can now use rvalue references to solve the perfect forwarding problem as set forth in the previous section. Here's what the solution looks like:

``` C++
template<typename T, typename Arg> 
shared_ptr<T> factory(Arg&& arg)
{ 
  return shared_ptr<T>(new T(std::forward<Arg>(arg)));
} 
```

where std::forward is defined as follows:

``` C++
template<class S>
S&& forward(typename remove_reference<S>::type& a) noexcept
{
  return static_cast<S&&>(a);
} 
```

(Don't pay attention to the noexcept keyword for now. It lets the compiler know, for certain optimization purposes, that this function will never throw an exception. We'll come back to it in Section 9.) To see how the code above achieves perfect forwarding, we will discuss separately what happens when our factory function gets called on lvalues and rvalues. Let A and X be types. Suppose first that factory<A> is called on an lvalue of type X:

``` C++
X x;
factory<A>(x);
```

Then, by the special template deduction rule stated above, factory's template argument Arg resolves to X&. Therefore, the compiler will create the following instantiations of factory and std::forward:

``` C++
shared_ptr<A> factory(X& && arg)
{ 
  return shared_ptr<A>(new A(std::forward<X&>(arg)));
} 

X& && forward(remove_reference<X&>::type& a) noexcept
{
  return static_cast<X& &&>(a);
} 
```

After evaluating the remove_reference and applying the reference collapsing rules, this becomes:

``` C++
shared_ptr<A> factory(X& arg)
{ 
  return shared_ptr<A>(new A(std::forward<X&>(arg)));
} 

X& std::forward(X& a) 
{
  return static_cast<X&>(a);
} 
```

This is certainly perfect forwarding for lvalues: the argument arg of the factory function gets passed on to A's constructor through two levels of indirection, both by old-fashioned lvalue reference.

Next, suppose that factory<A> is called on an rvalue of type X:

``` C++
X foo();
factory<A>(foo());
```

Then, again by the special template deduction rule stated above, factory's template argument Arg resolves to X. Therefore, the compiler will now create the following function template instantiations:

``` C++
shared_ptr<A> factory(X&& arg)
{ 
  return shared_ptr<A>(new A(std::forward<X>(arg)));
} 

X&& forward(X& a) noexcept
{
  return static_cast<X&&>(a);
} 
```

This is indeed perfect forwarding for rvalues: the argument of the factory function gets passed on to A's constructor through two levels of indirection, both by reference. Moreover, A's constructor sees as its argument an expression that is declared as an rvalue reference and does not have a name. By the no-name rule, such a thing is an rvalue. Therefore, A's constructor gets called on an rvalue. This means that the forwarding preserves any move semantics that would have taken place if the factory wrapper were not present.

It is perhaps worth noting that the preservation of move semantics is in fact the only purpose of std::forward in this context. Without the use of std::forward, everything would work quite nicely, except that A's constructor would always see as its argument something that has a name, and such a thing is an lvalue. Another way of putting this is to say that std::forward's purpose is to forward the information whether at the call site, the wrapper saw an lvalue or an rvalue.

If you want to dig a little deeper for extra credit, ask yourself this question: why is the remove_reference in the definition of std::forward needed? The answer is, it is not really needed at all. If you use just S& instead of remove_reference<S>::type& in the defintion of std::forward, you can repeat the case distinction above to convince yourself that perfect forwarding still works just fine. However, it works fine only as long as we explicitly specify Arg as the template argument of std::forward. The purpose of the remove_reference in the definition of std::forward is to force us to do so.

Rejoice. We're almost done. It only remains to look at the implementation of std::move. Remember, the purpose of std::move is to pass its argument right through by reference and make it bind like an rvalue. Here's the implementation:

``` C++
template<class T> 
typename remove_reference<T>::type&&
std::move(T&& a) noexcept
{
  typedef typename remove_reference<T>::type&& RvalRef;
  return static_cast<RvalRef>(a);
} 
```

Suppose that we call std::move on an lvalue of type X:

``` C++
X x;
std::move(x);
```

By the new special template deduction rule, the template argument T will resolve to X&. Therefore, what the compiler ends up instantiating is

``` C++
typename remove_reference<X&>::type&&
std::move(X& && a) noexcept
{
  typedef typename remove_reference<X&>::type&& RvalRef;
  return static_cast<RvalRef>(a);
} 
```

After evaluating the remove_reference and applying the new reference collapsing rules, this becomes

``` C++
X&& std::move(X& a) noexcept
{
  return static_cast<X&&>(a);
} 
```

That does the job: our lvalue x will bind to the lvalue reference that is the argument type, and the function passes it right through, turning it into an unnamed rvalue reference.

I leave it to you to convince yourself that std::move actually works fine when called on an rvalue. But then you may want to skip that: why would anybody want to call std::move on an rvalue, when its only purpose is to turn things into rvalues? Also, you have probably noticed by now that instead of

``` C++
std::move(x);
```

you could just as well write

``` C++
static_cast<X&&>(x);
```

However, std::move is strongly preferred because it is more expressive. 