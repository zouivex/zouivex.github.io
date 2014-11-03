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
2. 假设`widget`是多态类型，推荐的返回类型是什么？解释你的答案，以及其利弊。
3. 你决定按照上面的建议修改返回类型，但是一开始你担心这样会破坏与既有的调用代码的兼容性，如果只是重新编译调用代码还可以忍受，但是如果不得不全部修改调用代码则是万万不能忍受的。然后你突然灵光一现，意识到这是一个全新的项目，并且调用代码使用了现代C++惯用法，然后你大胆地继续修改返回类型，因为你知道现有的调用代码不需要任何修改。为什么你会如此自信？
4. 如果`widget`不是多态类型，那么推荐的返回类型是什么？请解释。

# 解答

## 此返回值有什么问题？

首先，上面简短的问题描述传达了什么信息？

题目告诉我们`load_widget`是一个工厂函数，它通过某种方式导入并创建新对象然后将对象返回给调用函数。由于返回类型是一个指针，那么返回值有可能为空。

调用函数对工厂函数创建的对象的使用方式，要么通过返回的指针调用成员函数，要么将指针作为参数传递给其它函数，或者其它的方式。直接使用返回的裸指针是不安全的，除非调用函数拥有返回的对象：要么调用函数独享对象，要么工厂函数在内部维护对象的强引用或弱引用信息。

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

> 准则：不要直接使用`new`，`delete`操作符，不要直接使用裸指针，除非特殊情况下代码位于封装的数据结构的底层。

第二，函数签名没有提供关于返回类型的更多的有用的信息。函数的文档可能会说明调用代码如何拥有对象，但是函数的声明并没有任何说明，调用代码只知道该对象要么是独享所有权，要么是共享所有权，但是不清楚具体是哪种。这种情况下，需要阅读并记住函数的文档，因为函数的声明没有提供任何相关信息。函数签名本身甚至没有说明调用代码是否共享所有权。

## 假设`widget`是多态类型，推荐的返回类型是什么？解释你的答案，以及其中的权衡。

如果widget类型是一个多态类型，调用函数通过持有其指针或引用的方式使用，那么工厂函数应该返回`unique_ptr`（转移所有权到调用代码）或`shared_ptr`（通过在内部数据结构中持有强引用的方式共享所有权）。

> 准则：对于返回引用类型的工厂函数，首选返回`unique_ptr`，需要共享所有权时返回`shared_ptr`。

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

一些人或许会问“我们不还是可以写`load_widget(some_id).release()`这样的代码吗？”。当然可以这样用，但是这样就有点钻牛角尖了。正确的回答是“不要这样用”。记住，我们的目标是避免Murphy定律，而不是解决成心造出的bug和错误，也没法对付故意写出的奇奇怪怪的代码（那种钻牛角尖式的代码就归为这一类）。这种用法就像C#语言在using代码块中提前销毁对象，java语言在try-with-resources代码块中提前close一样，没有违反类型安全性但是代码是错误的。

要是清除资源的代码不能简单使用delete调用完成呢？很简单，使用自定义deleter。最精妙之处在于，工厂函数知道调用哪个deleter，并且在构建对象的时候就明确指出，从而调用函数不必操心deleter的事情，特别是使用auto声明返回值的时候。

其次，这样的代码能够自动说明其意图，返回一个`unique_ptr`的函数清楚表明该函数是一个纯source函数，而返回一个`shared_ptr`的函数则清楚表明函数共享对象的所有权或者拥有观察者。

最后，为什么在不需要共享所有权时首选使用`unique_ptr`？因为使用`unique_ptr`对于性能和正确性来说都是正确的做法，在GotW89中还提到这样还给了调用函数选用其它智能指针的自由。

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

如果工厂函数需要保持共享引用或者观察引用（通过内部的`shared_ptr`或者`weak_ptr`）那么就返回`shared_ptr`。此时调用函数强制将返回值继续作为`shared_ptr`使用，只不过此时使用`shared_ptr`是合理的。

## 为什么能自信地将裸指针替换为`unique_ptr`？

现代的可扩展C++代码广泛使用`unique_ptr`，`shared_ptr`以及`auto`。如果返回`unique_ptr`则可以配合使用这3种对象，如果返回`shared_ptr`则只能配合使用后面两种对象。

如果调用代码用auto捕捉返回变量，如`auto w = load_widget(whatever);`，那么返回变量的类型自动是正确的，解引用操作也能正常工作，唯一可能导致代码改动的是显式调用delete操作符（此时delete所在的代码行可以被安全地删掉）或者试图将变量存入其它类型的对象中。

> 准则：请使用`auto`声明变量。使用`auto`使代码更简短，并且能将你的代码和不必要的的代码变动隔离开。

如果调用代码没有使用`auto`，那么极有可能将返回值初始化为`unique_ptr`或者`shared_ptr`，因为现代C++代码一般情况不直接使用裸指针。无论是`unique_ptr`还是`shared_ptr`，返回`unique_ptr`都能正常工作：`unique_ptr`可以无缝地移动到`unique_ptr`和`shared_ptr`，如果返回值表达的是共享所有权的语义，那么调用函数一般使用`shared_ptr`，此时使用`auto`依然能够工作（只会比显式指定变量类型更好，其原因是，为了返回裸指针，返回类型可能被强制跳过了`enable_shared_from_this`循环，如果直接返回`shared_ptr`并不需要此循环）。

## 如果`widget`不是多态类型，那么推荐的返回类型是什么？请解释。

如果widget不是多态类型，通常意味着这是一个可以复制的值对象或者是只能移动的对象，此时工厂函数应该按值返回widget对象。到底返回什么样类型的值呢？

在C++98中，程序员往往以返回指针的方式返回一个大的对象以避免复制对象造成的开销：

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

上面的代码有我们第一条中讨论过的所有使用上和安全上的问题。在现代C++种，一般情况下应该直接返回对象，因为将对象传递到调用函数只不过会触发一个移动操作，而不会触发深拷贝。

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

大部分情况下，可以按值返回可移动的对象。如果返回指针的唯一目的是避免复制的话，那么按值返回对象才是正确的做法。

可能还有一种情况，函数返回指针，那就是用空指针表示创建对象失败。一般情况下，载入widget对象失败时抛出异常要更好一些。然而，如果载入widget对象失败被看作是一种正常的情况的话，则返回`optional<widget>`对象，如果没有其它类型的错误，所有错误都可以用空`optional<widget>`对象表达时，将工厂函数声明为`noexcept`：

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

> 准则：如果工厂函数创建非引用类型的对象，那么应该默认按值返回对象，当创建对象出错时抛出异常。如果对象创建失败是一种正常情况的话，那么就返回`optional<>`对象。

# 尾声

注意到上面代码最后一行的`if(v)`测试没有？它调用了`optional<T>`对象的一个功能强大的`bool`操作符函数。为什么`bool`操作符功能这么强大？其中一个原因是它应用了很多C++的功能。下面的代码就是它的声明，请思考它能让我们安全地实现什么功能（包括编译期）？

``` C++
constexpr explicit optional<T>::operator bool() const noexcept;
```
