Title: GotW-90 智能指针在工厂模式中的使用
Slug: factories
Date: 2014-11-02 12:06:47
Modified: 2014-11-02 12:06:47
Category: 译文
Tags: cpp

工厂函数该返回什么类型的值，为什么？

# 问题

你最近开始参与一个新项目，在浏览代码库时，发现工厂函数的声明如下：

``` C++
widget* load_widget( widget::id desired );
```

1. 此返回值有什么问题？
2. 假设`widget`是多态类型，推荐的返回类型是什么？解释你的答案，以及其中的权衡。
3. 你决定按照上面的建议修改返回类型，但是一开始你担心这样会破坏与既有的调用代码的兼容性，如果只是重新编译调用代码还可以忍受，但是如果不得不全部修改调用代码则万万不能忍受的。然后某一时刻你会突然灵光一现，意识到现在是一个全新的项目，并且你的调用代码使用了现代C++惯用法，然后你大胆地继续修改返回类型，因为你知道现有的调用代码不需要任何修改。为什么你会如此自信？
4. 如果`widget`不是多态类型，那么推荐的返回类型是什么？请解释。

# 解答

## 此返回值有什么问题？

首先，上面简短的问题描述传达了什么信息？

题目告诉我们`load_widget`是一个工厂函数，它通过某种方式导入并创建新对象然后将对象返回给调用函数。由于返回类型是一个指针，那么返回值有可能为空。

调用函数使用工厂函数创建的对象，要么通过返回的指针调用成员函数，要么将指针作为参数传递给其它函数，或者用其它的方式使用。直接使用返回的裸指针是不安全的，除非调用函数拥有返回的对象：要么调用函数独享对象，要么工厂函数在内部维护对象的强引用或弱引用信息。

由于调用函数独享或者共享所有权，它必须在对象不再需要时执行一些操作。如果是独享所有权的情况，调用函数必须负责销毁对象，如果是共享所有权的情况，调用函数必须负责递减引用计数。

不幸的是，返回`widget*`指针有两个大问题。

第一，返回裸指针在默认情况下是不安全的，因为函数的默认行为是泄漏widget对象：

``` C++
// Example 1: Leak by default. Really, this is just so 20th-century...
//
widget* load_widget( widget::id desired );

:::

load_widget( some_id ); // oops
```

上面的代码能够成功编译，成功运行，然后widget对象发生泄漏（译注：即没有释放申请的内存）。

> 准则：不要直接使用`new`，`delete`操作符以及持有裸指针，除非在某些特殊情况下代码位于封装的数据结构的底层。

第二，函数签名没有提供关于返回类型的更多的有用的信息。函数的文档可能会说明调用代码如何拥有对象，但是函数的声明并没有任何说明，调用代码只知道要么该对象要么是独享所有权，要么是共享所有权，但是不清楚具体是哪种。这种情况下，需要阅读并记住函数的文档，因为函数的声明没有提供任何相关信息。函数签名本身甚至没有说明调用代码是否共享所有权。

## 假设`widget`是多态类型，推荐的返回类型是什么？解释你的答案，以及其中的权衡。

如果widget类型是一个多态类型，调用函数通过持有其指针或引用的方式使用，那么工厂函数应该返回`unique_ptr`（转移所有权到调用代码）或`shared_ptr`（通过在内部数据结构中持有强引用的方式共享所有权）。

> 准则：返回引用类型的工厂函数首选返回`unique_ptr`，需要共享所有权时返回`shared_ptr`。

这样解决了两个问题：安全性，自说明的文档。

首先，看看这样如何解决上面代码中的安全问题：

``` C++
// Example 2: Clean up by default. Much better...
//
unique_ptr<widget> load_widget( widget::id desired );

:::

load_widget( some_id ); // cleans up
```

上面例子中的代码能够成功编译、成功运行、并且高高兴兴地自动清除widget对象。它不光在一般情况下是安全的，这种代码从结构上能保证安全性，因为用户根本没有犯错误导致发生内存泄漏的机会。

一些人或许会问“我们不还是可以写`load_widget(some_id).release()`这样的代码吗？”。当然可以这样用，但是这样就有点钻牛角尖了。正确的回答是“不要这样用”。记住，我们的目标是避免Murphy定律，而不是避免成心造出的bug和错误，也没法对付故意写出的奇奇怪怪的代码（那种钻牛角尖式的代码就归为这一类）。这种用法就像C#语言在using代码块中提前销毁对象，java语言在try-with-resources代码块中提前close一样，没有违反类型安全性但是代码是错误的。

要是清除资源的代码不能简单使用delete调用完成呢？很简单，使用自定义deleter。最精妙之处在于，工厂函数知道调用哪个deleter，并且在构建返回值的时候就明确指出，从而调用函数不必操心deleter的事情，特别是使用auto声明返回值的时候。

其次，这样的代码能够自动说明其意图，返回一个unique_ptr的函数清楚表明该函数是一个纯source函数，而返回一个shared_ptr的函数则清楚表明函数共享所有权或者观察者的关系。

最后，为什么在不需要共享所有权时首选使用unique_ptr？因为使用unique_ptr对于性能和正确性来说都是正确的做法，在GotW89中还提到这样还给予调用函数选用其它智能指针的自由。

返回`unique_ptr`表达了返回单一所有权的意图，这是标准的纯"source"工厂函数。`unique_ptr`在性能方面无与伦比，因为move一个对象的开销就和move/copy裸指针差不多。如果调用函数希望能够通过`shared_ptr`管理对象的生命期，可以很容易地将`unique_ptr`通过move操作转换为`shared_ptr`。在此没有必要使用`std::move`，因为编译器已经知道返回值是一个临时对象。如果调用函数使用其它任意的方法来管理对象生命期，可以简单地通过调用`.release()`将其转换为自定义的智能指针或者其它的对象生命期管理方法。这个特性非常有用，但是`shared_ptr`不可能做到。下面是具体的代码：

``` C++
// Example 2, continued
//

// Accept as a unique_ptr (by default)
auto up = load_widget(1);

// Accept as a shared_ptr (if desired)
auto sp = shared_ptr<widget>{ load_widget(2) };

// Accept as your own smart pointer (if desired)
auto msp = my::smart_ptr<widget>{ load_widget(3).release() };
```

如果工厂函数持有共享的所有权或者是观察引用，通过内部的`shared_ptr`或者`weak_ptr`，那么就返回`shared_ptr`。此时调用函数将被迫将返回值继续作为`shared_ptr`使用，只不过此时这种行为是合理的。

## 为什么能自信地将裸指针替换为`unique_ptr`？

现代的可扩展C++代码广泛使用unique_ptr，shared_ptr以及auto。如果返回unique_ptr则可以配合使用它们仨，如果返回shared_ptr则只能配合使用后面两种。

If the caller accepts the return value in an auto variables, such as `auto w = load_widget(whatever);`, then the type will just naturally be correct, normal dereferencing will just work, and the only source ripple will be if the caller tries to explicitly delete (if so, the delete line can rather appropriately be deleted) or tries to store into a non-local object of a different type.

> Guideline: Prefer declaring variables using auto. It’s shorter, and helps to insulate your code from needless source ripples due to minor type changes.

Otherwise, if the caller isn’t using auto, then it’s likely already using the result to initialize a unique_ptr or shared_ptr because modern C++ calling code does not traffick in raw pointers for non-parameter variables (more on this next time). In either case, returning a unique_ptr just works: A unique_ptr can be seamlessly moved into either of those types, and if the semantics are to return shared ownership and then the caller should already be using a shared_ptr and things will again work just fine (only probably better than before, because for the original return by raw pointer to work correctly the return type was probably forced to jump through the enable_shared_from_this hoop, which isn’t needed if we just return a shared_ptr explicitly).

## 如果`widget`不是多态类型，那么推荐的返回类型是什么？请解释。

If widget is not a polymorphic type, which typically means it’s a copyable value type or a move-only type, the factory should return a widget by value. But what kind of value?

In C++98, programmers would often resort to returning a large object by pointer just to avoid the penalty of copying its state:

``` C++
// Example 4(a): Obsolete convention: return a * just to avoid a copy
//
/*BAD*/ vector<gadget>* load_gadgets() {
    vector<gadget>* ret = new vector<gadget>();
    // ... populate *ret ...
    return ret;
}

// Obsolete calling code (note: NOT exception-safe)
vector<gadget>* p = load_gadgets();
if(p) use(*p);
delete p;
```

This has all of the usability and fragility problems discussed in #1. Today, normally we should just return by value, because we will incur only a cheap move operation, not a deep copy, to hand the result to the caller:

``` C++
// Example 4(b): Default recommendation: return the value
//
vector<gadget> load_gadgets() {
    vector<gadget> ret;
    // ... populate ret ...
    return ret;
}

// Calling code (exception-safe)
auto v = load_gadgets();
use(v);
```

Most of the time, return movable objects by value. That’s all there is to it, if the only reason for the pointer on the return type was to avoid the copy.

There could be one additional reason the function might have returned a pointer, namely to return nullptr to indicate failure to produce an object. Normally it’s better throw an exception to report an error if we fail to load the widget. However, if not being able to load the widget is normal operation and should not be considered an error, return an optional<widget>, and probably make the factory noexcept if no other kinds of errors need to be reported than are communicated well by returning an empty optional<widget>.

``` C++
// Example 4(c): Alternative if not returning an object is normal
//
optional<vector<gadget>> load_gadgets() noexcept {
    vector<gadget> ret;
    // ... populate ret ...
    if( success )            // return vector (might be empty)
        return move(ret);    // note: move() here to avoid a silent copy
    else
        return {};           // not returning anything
}

// Calling code (exception-safe)
auto v = load_gadgets();
if(v) use(*v);
```

> Guideline: A factory that produces a non-reference type should return a value by default, and throw an exception if it fails to create the object. If not creating the object can be a normal result, return an optional<> value.

# Coda
By the way, see that test for if(v) in the last line of Example 4(c)? It calls a cool function of optional<T>, namely operator bool. What makes bool so cool? In part because of how many C++ features it exercises. Here is its declaration… just think of what this lets you safely do, including at compile time! Enjoy.

``` C++
constexpr explicit optional<T>::operator bool() const noexcept;
```

Acknowledgments
Thanks in particular to the following for their feedback to improve this article: Johannes Schaub, Leo, Vincent Jacquet.
