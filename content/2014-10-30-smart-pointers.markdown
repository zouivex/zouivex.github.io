Title: GotW-89 智能指针
Slug: smart-pointers
Date: 2014-10-30 21:22:04
Modified: 2014-10-30 21:22:04
Category: 译文
Tags: cpp

C++智能指针真是让人爱不释手，尤其是`unique_ptr`。

# 问题

1. 什么时候使用`shared_ptr`，什么时候使用`unique_ptr`？给出尽量多的理由。
2. 为什么几乎总是应该使用`make_shared`创建`shared_ptr`？请解释。
3. 为什么几乎总是应该使用`make_unique`创建`unique_ptr`？请解释。
4. `auto_ptr`都有哪些需要注意的问题？

# 解答
## 什么时候使用`shared_ptr`，什么时候使用`unique_ptr`？

如果拿不准该使用哪种智能指针时，那么就使用`unique_ptr`，将来确有需要时总是可以`move-convert`为`shared_ptr`。如果从一开始就清楚需要共享所有权，那么就直接使用`make_shared`函数创建`shared_ptr`（在第二节详细介绍）.

我们说“拿不准时，使用`unique_ptr`”，有三个主要的原因。

第一，最简单的语义就足够满足需求，使用正确的智能指针可以直接表达意图和（当前的）需求。如果对于新创建的对象，不清楚最终是否需要共享所有权，那么使用`unique_ptr`表达单一的所有权。`unique_ptr`仍然可以存入容器（例如，`vector<unique_ptr<widget>>`，以及执行大部分裸指针可以完成的操作，只会比裸指针更安全。将来需要共享所有权时，`unique_ptr`总是可以`move-convert`为`shared_ptr`。

第二，`unique_ptr`比`shared_ptr`效率更高。`unique_ptr`不需要维护引用计数信息和底层的控制块，它就是设计来像裸指针那样高效地移动和使用的。如果当前功能足够使用，就不要要求更多的功能，这样不用付出额外的不必要的开销。

第三，`unique_ptr`可扩展性更强，以后可选择的余地更多。如果当前使用的是`unique_ptr`，将来总是可以通过`move`转换为`shared_ptr`，或者调用`.get()`或者`.release()`转换为用户自定义的智能指针（甚至裸指针）。

准则：最好使用标准的智能指针，一般情况下使用`unique_ptr`，需要共享所有权时使用`shared_ptr`。所有的C++库都支持这两种标准智能指针。只有在需要和其它库交互时，或者标准的智能指针提供的`deleters`和`allocators`不能满足用户自定义的要求时，才考虑使用其它智能指针，

## 为什么几乎总是应该使用`make_shared`创建`shared_ptr`？请解释。

注意：在少数情况下，需要使用自定义分配器来创建对象，此时可以使用`allocate_shared`。即使名字不同，`allocate_shared`可以看作是`make_shared`的可以指定分配器的特殊版本。所以本文将它们都称为`make_shared`，而不分别介绍了。

在以下两种情况不能使用`make_shared`创建由`shared_ptr`管理的对象：

* 需要自定义`deleter`时。例如需要使用`shared_ptr`管理非内存的资源，或者从非内存区域分配而来的对象。因为`make_shared`不支持用户指定`deleter`。
* 使用从其它代码（通常是遗留代码）中传递过来的裸指针时，必须从裸指针直接构造`shared_ptr`。

准则：使用`make_shared`（如果需要自定义分配器，使用`allocate_shared`）创建由`shared_ptr`管理的对象，除非需要使用自定义的`deleter`或者需要处理从别处传递而来的裸指针。

那么，为什么几乎所有场合都应该使用`make_shared`呢？主要有两个原因：简单、效率。

第一，`make_shared`使代码更简单。代码应该以清晰和正确为上。

第二，`make_shared`更有效率。`shared_ptr`的实现中，需要在内部控制块维护管理信息，这些管理信息被所有指向同一对象的`shared_ptr`和`weak_ptr`所共享。尤其注意，管理信息必须包含两个引用计数：

* “强引用计数”，用来跟踪当前指向共享对象的`shared_ptr`的个数。共享对象在最后一个强引用释放之后被销毁（有可能此时内存被回收）。
* “弱引用计数”，用来跟踪当前正在观察共享对象的`weak_ptr`的个数。存放管理信息的控制块在最后一个弱引用释放之后被销毁并回收内存，如果共享对象的内存尚未回收，那么回收内存。

如果使用`new`表达式独立分配对象，然后将其传递给`shared_ptr`，那么`shared_ptr`的实现没有其它选择，只能独立分配控制块。参见下面例子和例图：

``` C++
// Example 2(a): Separate allocation
auto sp1 = shared_ptr<widget>{ new widget{} };
auto sp2 = sp1;
```
![Approximate memory layout for Example 2(a)]({filename}/images/)

在此最好避免对象和控制块单独分配。如果使用`make_shared`一次性分配对象和`shared_ptr`本身，那么编译器能够将它们合并到同一分配中。参见下面例子和例图：

``` C++
// Example 2(b): Single allocation
auto sp1 = make_shared<widget>();
auto sp2 = sp1;
```
![Approximate memory layout for Example 2(b)]({filename}/images/)

将对象和控制块合并分配有两个好处：

* 降低内存分配的开销，减少内存碎片。首先，降低内存开销最明显的方式是减少内存分配的请求次数，因为内存分配请求的开销很大。这还可以帮助减少分配器的多线程竞争，因为某些分配器的扩展性很差。其次，使用一次内存分配而不是两次，能够降低单次内存分配的开销。任何时候向系统申请一块内存，系统返回的字节数必须至少满足要求，由于系统使用固定大小的内存池或以每次分配为单位跟踪内存管理信息，系统通常都会返回额外的字节。因此，使用单个内存块，能够降低总的内存开销。最后，这种方法自然而然地降低了内存块之间间隔的无用内存，从而避免了内存碎片。
* 增强程序的局部性。引用计数和共享的对象一起被频繁地访问，对于小的对象，它们极有可能位于同一个cache行中，因此能够提升cache访问的性能。

通过一个函数调用表达你的意图，系统计算出效率更高的方法的机会就更大。将100个元素插入vector时，调用一次`.insert(first, last)`插入100个元素，比调用100次`.insert(value)`每次插入一个元素效率要高。同样的道理，调用一次`make_shared`比分别调用`new widget()`和`shared_ptr(widget*)`效率高。

此外`make_shared`还有两个好处：`make_shared`避免了直接调用`new`表达式，也免了异常安全的问题。这两个好处也适用于`make_unique`函数，在下一节中我们详细介绍。

## 为什么几乎总是应该使用`make_unique`创建`unique_ptr`？请解释。

和`make_shared`一样，两种情况下不能使用`make_unique`创建由`unique_ptr`管理的对象：需要使用自定义的`deleter`时，需要操作裸指针时。除此之外的任何情况请使用`make_unique`。

准则：除非需要使用自定义的deleter或者需要操作从别处传入的裸指针，一般情况下推荐使用`make_unique`创建无需共享所有者的对象。

除了与`make_shared`相应的优点以外，`make_unique`还有其它优点。第一，和功能更强的`unique_ptr<T>{ new T{} }`相比，优先使用`make_unique<T>()`。通常应该避免直接使用new操作符。

准则： 不要使用new，delete操作符直接持有裸指针，除非在某些特殊情况下需要操作封装在底层的数据结构的裸指针。

第二，可以避免使用new操作符导致的众所周知的异常安全问题，参见以下的例子：

``` C++
void sink( unique_ptr<widget>, unique_ptr<gadget> );

sink( unique_ptr<widget>{new widget{}},
      unique_ptr<gadget>{new gadget{}} ); // Q1: do you see the problem?
```

简单来说，如果先分配和构造widget对象，在分配和构造时抛出一个异常，那么widget对象发生内存泄漏。你或许会这样想：“用`make_unique<widget>()`替换`new widget{}`，可以解决这个问题，是吗？”。请参考下面的代码：

``` C++
sink( make_unique<widget>(),
      unique_ptr<gadget>{new gadget{}} ); // Q2: is this better?
```

不对，因为C++对于函数参数的求值顺序是未定义的，所以先创建widget对象和先创建gadget对象都有可能。如果先创建gadget对象，然后执行`make_unique<widget>`时抛出异常，那么同样有内存泄漏问题发生。

但是只是修改其中一个参数使用`make_unique`并不能解决问题，如果将两个参数都修改为`make_unique`能够完整地解决这个问题：

``` C++
sink( make_unique<widget>(), make_unique<gadget>() ); // exception-safe
```

异常安全问题在GotW #56中有完整介绍。

准则：分配对象时，首选使用`make_unique`，如果对象有共享的生命期，那么使用`make_shared`。

## `auto_ptr`都有哪些需要注意的问题？

`auto_ptr`被认为是在C++没有move语义的时代尝试实现`unique_ptr`的勇敢的尝试。`auto_ptr`现在已经被弃用了，不要再在新代码中使用它。

如果在现有代码使用了`auto_ptr`，那么找个机会在所有代码中查找替换所有的`auto_ptr`为`unique_ptr`。它们的大部分使用方式是一样的，有可能通过编译错误的方式暴露出或者默默修复几个之前没有发现的bug。
