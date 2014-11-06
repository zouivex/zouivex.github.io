Title: GotW-91 智能指针参数
Slug: solution-smart-pointer-parameters
Date: 2014-11-05 20:21:31
Modified: 2014-11-05 20:21:31
Category: 译文
Tags: cpp

如何将智能指针作为参数传递？为什么？

# 问题

1. 下面函数声明的性能如何？请解释。
``` C++
void f( shared_ptr<widget> );
```

2. 上面的函数声明的正确性如何？请举例解释你的答案。

3. 你的同事写了一个函数使用`widget`类型作为输入参数，他有以下几种基本的参数选择（此处忽略`const`）：

``` C++
void f( widget* );              (a)
void f( widget& );              (b)
void f( unique_ptr<widget> );   (c)
void f( unique_ptr<widget>& );  (d)
void f( shared_ptr<widget> );   (e)
void f( shared_ptr<widget>& );  (f)
```

它们都适合在什么情况下使用？解释你的答案，同时解释是否应该为参数类型加上`const`。其实还有其它的参数传递方式，但是我们只考虑上面提到的几种。

# 解答

## 下面函数声明的性能如何？请解释。
``` C++
void f( shared_ptr<widget> );
```

`shared_ptr`内部存有强引用计数和弱引用计数（参见GotW #89）。若以传值方式传递，那么通常在函数的入口处对传入参数进行复制，然后在函数出口处销毁。让我们对此进行详细剖析。

在函数入口处，参数`shared_ptr`被拷贝构造，同时还需要递增强引用计数。（是的，如果调用函数传入的是一个临时的`shared_ptr`，只需进行移动构造从而无需修改引用计数。但是，(a)在一般代码中使用临时shared_ptr的情况很少，一般都是将函数的返回值立即传递给另一个函数；(b)而且我们将看到函数的性能开销主要耗费在参数的销毁上。）

在函数的出口处，shared_ptr参数被销毁，此时需要递减内部的引用计数。

递增和递减递减共享的引用计数有什么不好的方面呢？两方面，其一与”共享的引用计数“相关，其二与”递增和递减引用计数“相关。弄明白引用计数对性能造成影响的两个原因对我们非常有好处：其中一个很重要并且很普遍，另一个不大可能发生在设计良好的代码中，故而相对不那么重要。

第一，递增递减操作导致的性能开销是一个重要的原因：因为引用计数是一个共享的原子变量（或类似的变量），对其进行递增递减在内部其实是进行同步的"读-修改-写"模式的内存操作。

第二，另一个相对不重要的原因是”共享引用计数“在进行大规模扩展时会发生争用：递增和递减操作都会更新引用计数，即是说在处理器和内存层面同一时刻只有一个CPU核能在同一个引用计数变量上执行指令，因为此操作需要对引用计数所在的cache行进行独占的访问。其结果是在访问引用计数的cache行时会发生争用，例如在密集的循环中，多个线程同时访问同一个cache行，此时会严重影响可扩展性，例如两个线程在密集循环中调用类似的函数，并且同时访问指向同一个共享对象的shared_ptr。所以我们要大声疾呼，”用户们，请不要这样使用！“。其它都没有问题，只是用户并不总是知道两个线程中不同的两个shared_ptr其实指向的是同一个对象，so let’s not be quick to pile the wood around his stake just yet。

我们会看到，对于所有基于引用计数的智能指针都有一个基本的最佳实践，那就是避免进行拷贝，除非确实需要增加一个引用。这直接避免了上面介绍的两种影响性能的因素，从而大大降低了它们对大部分程序性能影响，特别是第二种因素，因为在密集循环中添加、移除引用是一种“反模式”。

此时此刻，我们会想到采用传引用的方式传递shared_ptr能解决上面的问题。但是这真的是一个正确的解决方案吗？还是要具体情况具体分析。

## 上面的函数声明的正确性如何？请举例解释你的答案。

在正确性上唯一的好处是函数清晰地、以类型强制的方式表明了函数将要（或者能够）复制一个shared_ptr对象。

That this is the only correctness implication might surprise some people, because there would seem to be one other major correctness benefit to taking a copy of the argument, namely lifetime: Assuming the pointer is not already null, taking a copy of the shared_ptr guarantees that the function itself holds a strong refcount on the owned object, and that therefore the object will remain alive for the duration of the function body, or until the function itself chooses to modify its parameter.

However, we already get this for free—thanks to structured lifetimes, the called function’s lifetime is a strict subset of the calling function’s call expression. Even if we passed the shared_ptr by reference, our function would as good as hold a strong refcount because the caller already has one—he passed us the shared_ptr in the first place, and won’t release it until we return. (Note this assumes the pointer is not aliased. You have to be careful if the smart pointer parameter could be aliased, but in this respect it’s no different than any other aliased object.)

> Guideline: Don’t pass a smart pointer as a function parameter unless you want to use or manipulate the smart pointer itself, such as to share or transfer ownership.

> 准则：通过传值、*、&的方式传递对象参数，而不要通过智能指针。

如果你要说：“难道裸指针没有弊端吗？”，非常好，我们在下面一节会讨论这个问题。

## 此处列出的智能指针参数使用方法都在什么情况下适用？

(a)和(b)：首选以*或者&的方式传递参数：

``` C++
void f( widget* );              (a)
void f( widget& );              (b)
```

These are the preferred way to pass normal object parameters, because they stay agnostic of whatever lifetime policy the caller happens to be using.

Non-owning raw * pointers and & references are okay to observe an object whose lifetime we know exceeds that of the pointer or reference, which is usually true for function parameters. Thanks to structured lifetimes, by default arguments passed to f in the caller outlive f‘s function call lifetime, which is extremely useful (not to mention efficient) and makes non-owning * and & appropriate for parameters.

Pass by * or & to accept a widget independently of how the caller is managing its lifetime. Most of the time, we don’t want to commit to a lifetime policy in the parameter type, such as requiring the object be held by a specific smart pointer, because this is usually needlessly restrictive. As usual, use a * if you need to express null (no widget), otherwise prefer to use a &; and if the object is input-only, write const widget* or const widget&.

(c) Passing unique_ptr by value means “sink.”
``` C++
void f( unique_ptr<widget> );   (c)
```
This is the preferred way to express a widget-consuming function, also known as a “sink.”

Passing a unique_ptr by value is only possible by moving the object and its unique ownership from the caller to the callee. Any function like (c) takes ownership of the object away from the caller, and either destroys it or moves it onward to somewhere else.

Note that, unlike some of the other options below, this use of a by-value unique_ptr parameter actually doesn’t limit the kind of object that can be passed to those managed by a unique_ptr. Why not? Because any pointer can be explicitly converted to a unique_ptr. If we didn’t use a unique_ptr here we would still have to express “sink” semantics, just in a more brittle way such as by accepting a raw owning pointer (anathema!) and documenting the semantics in comments. Using (c) is vastly superior because it documents the semantics in code, and requires the caller to explicitly move ownership.

Consider the major alternative:

``` C++
// Smelly 20th-century alternative
void bad_sink( widget* p );  // will destroy p; PLEASE READ THIS COMMENT

// Sweet self-documenting self-enforcing modern version (c)
void good_sink( unique_ptr<widget> p );
```
And how much better (c) is:

``` C++
// Older calling code that calls the new good_sink is safer, because
// it's clearer in the calling code that ownership transfer is going on
// (this older code has an owning * which we shouldn't do in new code)
//
widget* pw = ... ; 

bad_sink ( pw );             // compiles: remember not to use pw again!

good_sink( pw );             // error: good
good_sink( unique_ptr<widget>{pw} );  // need explicit conversion: good

// Modern calling code that calls good_sink is safer, and cleaner too
//
unique_ptr<widget> pw = ... ;

bad_sink ( pw.get() );       // compiles: icky! doesn't reset pw
bad_sink ( pw.release() );   // compiles: must remember to use this way

good_sink( pw );             // error: good!
good_sink( move(pw) );       // compiles: crystal clear what's going on
```

> Guideline: Express a “sink” function using a by-value unique_ptr parameter.

Because the callee will now own the object, usually there should be no const on the parameter because the const should be irrelevant.

(d) Passing unique_ptr by reference is for in/out unique_ptr parameters.
``` C++
void f( unique_ptr<widget>& );  (d)
```
This should only be used to accept an in/out unique_ptr, when the function is supposed to actually accept an existing unique_ptr and potentially modify it to refer to a different object. It is a bad way to just accept a widget, because it is restricted to a particular lifetime strategy in the caller.

> Guideline: Use a non-const unique_ptr& parameter only to modify the unique_ptr.

Passing a const unique_ptr<widget>& is strange because it can accept only either null or a widget whose lifetime happens to be managed in the calling code via a unique_ptr, and the callee generally shouldn’t care about the caller’s lifetime management choice. Passing widget* covers a strict superset of these cases and can accept “null or a widget” regardless of the lifetime policy the caller happens to be using.

> Guideline: Don’t use a const unique_ptr& as a parameter; use widget* instead.

I mention widget* because that doesn’t change the (nullable) semantics; if you’re being tempted to pass const shared_ptr<widget>&, what you really meant was widget* which expresses the same information. If you additionally know it can’t be null, though, of course use widget&.

(e) Passing shared_ptr by value implies taking shared ownership.
``` C++
void f( shared_ptr<widget> );   (e)
```
As we saw in #2, this is recommended only when the function wants to retain a copy of the shared_ptr and share ownership. In that case, a copy is needed anyway so the copying cost is fine. If the local scope is not the final destination, just std::move the shared_ptr onward to wherever it needs to go.

> Guideline: Express that a function will store and share ownership of a heap object using a by-value shared_ptr parameter.

Otherwise, prefer passing a * or & (possibly to const) instead, since that doesn’t restrict the function to only objects that happen to be owned by shared_ptrs.

(f) Passing shared_ptr& is useful for in/out shared_ptr manipulation.
``` C++
void f( shared_ptr<widget>& );  (f)
```
Similarly to (d), this should mainly be used to accept an in/out shared_ptr, when the function is supposed to actually modify the shared_ptr itself. It’s usually a bad way to accept a widget, because it is restricted to a particular lifetime strategy in the caller.

Note that per (e) we pass a shared_ptr by value if the function will share ownership. In the special case where the function might share ownership, but doesn’t necessarily take a copy of its parameter on a given call, then pass a const shared_ptr& to avoid the copy on the calls that don’t need it, and take a copy of the parameter if and when needed.

> Guideline: Use a non-const shared_ptr& parameter only to modify the shared_ptr. Use a const shared_ptr& as a parameter only if you’re not sure whether or not you’ll take a copy and share ownership; otherwise use widget* instead (or if not nullable, a widget&).
