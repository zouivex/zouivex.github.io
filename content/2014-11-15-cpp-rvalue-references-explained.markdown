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

既然我们理解了`std::move`，那么我们可以进一步讨论为什么对拷贝赋值运算符进行右值引用重载仍然有些问题。以下面变量的简单赋值操作为例：

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

# 右值引用本身是右值吗？

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

将使代码难以理解，并且非常容易出错，因为我们移动的对象，也就是刚被偷走的对象，在此后的代码中仍然可以访问。但是对于移动语义，将变量所绑定的对象移动之后立即释放此变量，用户"并不在意"时才可以使用。 所以，规则就是，”如果有名字，那么就是左值”。

那么对于规则的后半句，“如果没有名字那么就是右值”该怎么理解呢？以上面的goo类为例，虽然可能性不大，但是理论上第二行的表达式goo()指向的对象有可能在移动之后仍然可以访问。但是按照之前章节的介绍可知，有时候我们期望的就是这种行为！我们期望能够谨慎地对左值执行强制移动语义，“如果没有名字那么就是右值”这条规则恰好让我们达到这个目的。这就是`std::move`函数的工作原理。虽然现在还不是时候深入讨论std::move函数的具体实现，但是我们对它的理解已经进了一步。`std::move`的传入参数为引用类型，函数中没有其它任何操作，仅仅返回其参数的右值引用。所以此表达式：

``` C++
std::move(x)
```

声明为右值引用，并且没有名字，所以是右值。也就是说，`std::move`将传入的参数转换为右值，实现方式就是“隐藏变量的名字”。

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

考虑下面的函数定义：
``` C++
X foo()
{
  X x;
  // perhaps do something to x
  return x;
}
```

和前面一样，我们假设X类重载了拷贝构造函数和拷贝赋值运算符，实现了移动语义。如果仅仅从代码表面上看，可能会认为此时返回x对象会触发一次拷贝操作。那么我们强制执行移动语义：

``` C++
X foo()
{
  X x;
  // perhaps do something to x
  return std::move(x); // making it worse!
}
```

很不幸，这样不但不会提升性能，还有可能降低性能。所有的现代C++编译器对于这种情况都会进行返回值优化。即是说，编译器不是先在函数体中构造一个x对象然后将对象拷贝出去，而是直接对foo函数的返回值进行构造。很明显，这比使用移动语义还要好。

从这里可以看出，如果想要有效地使用右值引用和移动语义，需要深入了解当前的编译器的“特殊优化”，比如说返回值优化技术，以及拷贝消除技术。可以阅读Dave Abrahams关于这个主题的一系列[博客文章]()。个中细节相当繁杂，但是我们既然选择C++语言，自然有我们的道理，是不是？我们自己选择的路，跪着也要走完。

# 完美传递：问题定义

右值引用还用来解决完美传递问题。请看下面的简单工厂函数：

``` C++
template<typename T, typename Arg> 
shared_ptr<T> factory(Arg arg)
{ 
  return shared_ptr<T>(new T(arg));
} 
```

很明显，此函数的目的是将参数传递到T的构造函数。理想情况下，我们希望此处就像没有工厂函数一样，客户代码直接调用构造函数，即“完美传递”。上面的代码并没有实现完美传递，其调用链中有一步的参数是按值传递的，当构造函数需要传入引用参数时问题非常严重。

最常用的解决方案是使最外层的函数传入引用参数，`boost::bind`采用的就是这种方法：

``` C++
template<typename T, typename Arg> 
shared_ptr<T> factory(Arg& arg)
{ 
  return shared_ptr<T>(new T(arg));
} 
```

这种方法能够解决部分问题，但是还不够完美。此处的问题是，工厂函数不能传入右值：

``` C++
factory<X>(hoo()); // error if hoo returns by value
factory<X>(41); // error
```

提供一个传入const引用参数的重载函数即可解决这个问题：

``` C++
template<typename T, typename Arg> 
shared_ptr<T> factory(Arg const & arg)
{ 
  return shared_ptr<T>(new T(arg));
} 
```

但是这样又引出了两个问题：
* 第一，如果工厂函数的参数不止一个，那么我们需要为所有的参数类型组合提供重载函数。从而，当支持的参数个数增加时，此方法就无法扩展了。
* 第二，这种传递参数的方式不够完美，它不支持移动语义，因为工厂函数中传入T的构造函数的参数为左值。其结果是，即使对于那些支持移动语义的构造函数，我们也无法在工厂函数中使用移动语义。

我们可以使用右值引用解决这两个问题。通过使用右值引用我们可以实现真正的完美传递，而不需要采用函数重载。为了究其原因，下面我们要介绍右值引用的两条规则。

# 完美传递：问题求解

第一条规则也会影响到左值引用。回想在C++11之前的标准中，不允许取一个引用的引用，如`A& &`形式的代码将会编译失败。而在C++11中，加入了如下的引用折叠规则：

``` C++
A& & becomes A&
A& && becomes A&
A&& & becomes A&
A&& && becomes A&&
```

第二条规则，即对模板函数的右值引用参数的特殊的类型推导规则：

``` C++
template<typename T>
void foo(T&&);
```

应用此规则：

* 当函数foo传入类型为A的左值参数，则T解析为`A&`，按照上面的引用折叠规则，参数最终转换为`A&`
* 当函数foo传入类型为A的右值参数，则T解析为`A`，从而参数最终转换为`A&&`

有了这两条规则，我们现在可以使用右值引用来解决完美传递的问题了。下面的代码解决了完美传递问题：

``` C++
template<typename T, typename Arg> 
shared_ptr<T> factory(Arg&& arg)
{ 
  return shared_ptr<T>(new T(std::forward<Arg>(arg)));
} 
```

其中std::forward定义为：

``` C++
template<class S>
S&& forward(typename remove_reference<S>::type& a) noexcept
{
  return static_cast<S&&>(a);
} 
```

（此时可以暂时忽略`noexept`关键字，此关键字告诉编译器本函数不会抛出异常，这对某些编译器优化非常有帮助，我们将在第9节详细介绍）为了弄明白到底是如何实现完美传递的，我们分别讨论传入左值参数和右值参数的情况。我们假设A和X为类型，`factory<A>`函数传入类型为X的左值：

``` C++
X x;
factory<A>(x);
```

那么，按照特殊类型推导规则，factory的模板参数解析为`X&`。因此，编译器生成的factory函数和`std::forward`函数为：

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

对`remove_reference`求值和应用引用折叠规则之后，上面的函数转换为：

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

这就是对于左值参数的完美传递，即传入factory函数的参数通过了两层间接调用而传入了A的构造函数，保持了左值引用的方式。

下面让我们假设factory<A>传入参数为X类型的右值：

``` C++
X foo();
factory<A>(foo());
```

同样，通过特殊类型推导规则，factory的模板参数解析为X。因此，编译器生成如下的函数：

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

这对于右值参数来说也是完美传递的，即传入factory函数的右值参数通过了两层间接调用，保持了右值引用的方式。此外，A的构造函数只知道其传入参数声明为右值引用类型，并且没有名字。根据上面的没有名字的规则，这种参数为右值参数。因此，A的构造函数传入的是右值。即是说，此处的参数传递保持了调用链中的移动语义。

值得注意的是，保持移动语义是此处使用`std::forward`的唯一目的。如果不使用`std::forward`，那么一切将工作正常，只是A的构造函数传入参数有名字，因此它是一个左值。换句话说std::forward的目的是传递参数在初始调用处是左值还是右值的信息。

如果我们继续深究，那么请思考这个问题：为什么`std::forward`的定义中需要使用`remove_reference`？答案是，不使用它也行。如果简单地用S&代替`remove_reference<S>::type&`，那么我们依样画葫芦应用上面描述的规则可以得知完美传递也能正常工作。但是，完美传递需要我们明确指定`std::forward`的参数类型才能正常工作。那么`remove_reference`的目的就是强制让我们指定参数类型。

庆祝一下吧！我们基本上介绍完了。剩下的就是看看`std::move`的实现了。记住，`std::move`的目的是将传入的引用参数转换成右值。下面是具体实现：

``` C++
template<class T> 
typename remove_reference<T>::type&&
std::move(T&& a) noexcept
{
  typedef typename remove_reference<T>::type&& RvalRef;
  return static_cast<RvalRef>(a);
} 
```

假设我们传入`std::move`的参数为X类型的左值：

``` C++
X x;
std::move(x);
```

按照特殊类型推导规则，模板参数T解析为`X&`。编译器为此生成的函数为：

``` C++
typename remove_reference<X&>::type&&
std::move(X& && a) noexcept
{
  typedef typename remove_reference<X&>::type&& RvalRef;
  return static_cast<RvalRef>(a);
} 
```

对`remove_reference`求值以及应用引用折叠规则之后，函数转换为：

``` C++
X&& std::move(X& a) noexcept
{
  return static_cast<X&&>(a);
} 
```

这样就实现了我们的目标：传入的参数x将绑定到左值引用，而`std::move`将其转换为匿名的右值引用。

请读者自己推导一下传入参数为右值引用的情况。还是要顺便提一下：既然我们对于右值参数调用`std::move`的唯一目的是将其转换为右值，那么为什么还要调用`std::move`呢？同样，我们注意到除了调用：

``` C++
std::move(x);
```

我们其实可以直接调用：

``` C++
static_cast<X&&>(x);
```

无论如何，我们强烈推荐使用`std::move`，因为它能更好地表达我们的意图。

# 右值引用和异常处理

当使用C++语言开发软件时，我们可以选择关注软件的异常安全性，也可以根本不使用异常。而右值引用则不然，如果重载类的拷贝构造函数和拷贝赋值运算符实现移动语义，那么我们建议：

* 争取使重载函数不抛出异常。一般情况下，使用移动语义就是简单地交换两个对象中指向资源的指针或者handle，这对于我们来说不难实现
* 如果重载函数中不抛出异常，那么使用noexcept关键字通知其它函数

如果我们不这样做的话，那么至少在这种非常常见的情况下，我们不能使用移动语义，即`std::vector`改变大小的时候，此时我们希望将当前的元素移动到新分配的内存块中。但是如果上面两条不满足的话，就无法使用移动语义。

这种行为背后的原因非常复杂。详情请参看Dave Abrahams的[博客]()。需要注意，写作这篇博客的时候，还不知道可以使用noexcept关键字来解决这个问题。

# 关于隐式移动

在讨论右值引用的过程中，标准委员会一度认为移动构造函数和移动赋值运算符在用户没有自定义的时候应该由编译器自动生成。此需求表面上看非常合情合理，因为编译器对于拷贝构造函数和拷贝赋值运算符就是这样处理的。在2010年8月份，Scott Meyers在comp.lang.c++讨论组中发表了一篇文章说明编译器生成的移动构造函数可能破坏现有的代码。Dave Abrahams在他的博客中也总结了这个问题。

委员会之后确认了这确实可能导致问题，并且对编译器自动生成移动构造函数和移动赋值运算符进行限制，大大减小了破坏现有代码的可能性。Herb Sutter在他的这篇博客中总结了这个决定。

关于隐式移动的问题在C++标准定稿的时候依然有争议（例如，Dave Abrahams的这篇[博客]()）。也许是命运的作弄，标准委员会一开始引入隐式移动语义的主要目的是解决上面一节中讨论的异常安全的问题。由于之后引入了`noexcept`关键字，这个异常安全的问题就迎刃而解了。要是noexcept关键字早提出几个月的话，隐式移动语义的问题压根就不会有人提出来。好吧，现在已经这样了。

以上就是右值引用的全部内容。我们看到，它有其优点，但是细节上又很残酷。作为一个C++专业人员，我们必须弄明白个中缘由，否则我们就没有办法完全掌握我们吃饭的家伙。值得庆幸的是，在我们的日常编程工作中，对于右值引用我们只需要记住下面3条就足够了：
     
* 通过这样对函数进行重载：`void foo(X& x); void foo(X&& x);`，我们可以在编译期根据传入的参数是左值还是右值选择不同的函数。主要用于重载拷贝构造函数和拷贝赋值运算符，以实现移动语义。注意在过程中正确进行异常处理，尽量多地使用`noexcept`关键字
* `std::move`将左值参数转换为右值
* `std::forward`让我们实现参数的完美传递