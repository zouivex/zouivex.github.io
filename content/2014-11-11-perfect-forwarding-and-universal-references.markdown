Title: 完美传递和通用引用
Slug: perfect-forwarding-and-universal-references
Date: 2014-11-11 21:35:40
Modified: 2014-11-11 21:35:40
Category: 译文
Tags: cpp

C++11的许多新功能的目的是为了提升性能，容器类中的`emplace`系列方法就是其中之一。例如`std::vector`就有与`push_back`方法类似的`emplace_back`方法，以及与`insert`方法类似的`emplace`方法。

下面简单地展示这些新方法带来的好处：

``` C++
class MyKlass {
public:
  MyKlass(int ii_, float ff_) {...}

private:
  {...}
};

some function {
  std::vector<MyKlass> v;

  v.push_back(MyKlass(2, 3.14f));
  v.emplace_back(2, 3.14f);
}
```

跟踪`MyKlass`类构造函数和析构函数的执行过程，可以看到`push_back`方法的执行顺序如下：

* 执行`MyKlass`临时对象的构造函数
* 对实际插入到`vector`中的对象调用move构造函数
* 执行临时对象的析构函数

这确实需要执行很多操作。但是很多操作并不是必须的，很明显传递给`push_back`方法的对象是一个右值，在语句执行完毕之后就不再存在，所以没有理由在此构建一个临时对象（为什么不直接在`vector`中构建呢）？

`emplace_back`方法就是这样实现的。对于上面的`v.emplace_back(2, 3.14f)`调用，全部开销就是一次构造函数调用。对象直接在`vector`中构造，所以不需要创建临时对象。

其工作原理是直接调用`emplace_back`进行构造，然后将参数传递到`MyKlass`的构造函数中。这需要依靠C++11的两个新功能：可变参数模板和完美传递。本文将介绍完美传递的工作原理以及使用方法。

# 完美传递问题

令函数`func(E1, E2, ..., En)`使用泛型参数`E1，E2，...，En`，我们需要实现一个wrapper函数`wrapper(E1, E2, ..., En)`使其与`func(E1, E2, ..., En)`等价。也就是说，实现一个函数使其泛型参数完美地传递到其他函数。

上面讨论过的`emplace_back`方法就是此问题的一个实际例子。`vector<T>::emplace_back`将其参数传递到类型T的构造函数，而不关心T的具体类型是什么。

下面，我将展示一些代码实例，介绍如何在C++11之前的标准中实现此功能。为了简单起见，在此先不讨论可变参数模板，并且假设我们需要传递两个参数。

第一感，我们可以这样实现：

``` C++
template <typename T1, typename T2>
void wrapper(T1 e1, T2 e2) {
    func(e1, e2);
}
```

很明显，上面的代码在`func`函数传递引用参数时有问题，因为wrapper函数是按值传递参数的。如果func修改了其引用参数，此修改并不能传达到wrapper的调用函数中（参数修改只影响wrapper函数的一份拷贝）。

那好，我们可以修改wrapper使其也传递引用参数。这样不会对func函数按值传递参数造成影响，因为此时在wrpper中调用func函数会对传入的参数进行复制。

``` C++
template <typename T1, typename T2>
void wrapper(T1& e1, T2& e2) {
    func(e1, e2);
}
```

但是这种方式有其他问题。因为右值不能绑定到引用参数上，因此下面的代码虽然合理，却会编译失败：

``` C++
wrapper(42, 3.14f);                  // error: invalid initialization of
                                     //        non-const reference from
                                     //        an rvalue

wrapper(i, foo_returning_float());   // same error
```

并且将引用参数限定为`const`也不能解决问题，因为对func函数传入非`const`的引用参数是很正当的要求。

剩下的唯一解决方案就是一些库所采用的暴力方法了：即为`const`和非`const`引用参数分别实现重载函数：

``` C++
template <typename T1, typename T2>
void wrapper(T1& e1, T2& e2)                { func(e1, e2); }

template <typename T1, typename T2>
void wrapper(const T1& e1, T2& e2)          { func(e1, e2); }

template <typename T1, typename T2>
void wrapper(T1& e1, const T2& e2)          { func(e1, e2); }

template <typename T1, typename T2>
void wrapper(const T1& e1, const T2& e2)    { func(e1, e2); }
```

这样的重载函数是指数级增长的。可以想象当函数参数稍微增加几个时，需要实现多少个重载函数。何况C++11还多增加了右值引用类型，对此类型我们也希望能正确地传递，上面的解决方法明显不可扩展。

# 引用折叠及右值引用的类型推导

在解释C++11如何解决完美传递问题之前，我们需要先解释C++中两条新增加的规则。

其中引用折叠规则比较容易解释，所以先介绍它。在之前的C++中取引用的引用是非法的。但是，在模板和类型推导中时常需要用到此规则：

``` C++
template <typename T>
void baz(T t) {
  T& k = t;
}
```

如果我们这样调用函数会发生什么事情？

``` C++
int ii = 4;
baz<int&>(ii);
```

在模板具现化时，T被显式设置为`int&`。那么内部的k的类型是什么呢？编译器看到的类型是`int& &`，但是这种形式程序员在代码中并不能直接写出来，所以编译器简单地将其推导为引用类型。事实上，在C++11之前，此行为并没有标准化，但是许多编译器支持这种行为，因为这样的代码在模板元编程中时常出现。C++11加入了右值引用类型，那么对引用累加的情况进行定义就非常重要了（比如，`int&& &`表示什么类型？）。

这就是引用折叠规则。规则非常简单，即永远以&为准。所以& &折叠为&，&& &以及& &&也折叠为&。折叠为&&的唯一的情况是&& &&。可以将此规则想象成逻辑或的关系，&为1，&&为0。 

另一个新加进C++11中的与本文相关规则是对于右值引用的类型推导规则[^1]。例如下面这个模板函数：

``` C++
template <class T>
void func(T&& t) {
}
```

不要被T&&迷惑，t并不是右值引用[^2]。在有类型推导场合，T&&表示特殊的语义。当func具现化时，类型T由传入func的参数是左值还是右值决定。如果传入的参数是类型为U的左值，那么T即推导为U&，如果传入的参数是右值，那么T被推导为U：

``` C++
func(4);            // 4 is an rvalue: T deduced to int

double d = 3.14;
func(d);            // d is an lvalue; T deduced to double&

float f() {...}
func(f());          // f() is an rvalue; T deduced to float

int bar(int i) {
  func(i);          // i is an lvalue; T deduced to int&
}
```

你可能觉得这个规则很奇葩，因为它就是那么奇葩。但是想想这个规则是用来解决完美传递问题的，就开始有那么点意思了。

# 使用`std::forward`解决完美传递问题

让我们回到wrapper模板函数吧。在C++11中应该这样实现：

``` C++
template <typename T1, typename T2>
void wrapper(T1&& e1, T2&& e2) {
    func(forward<T1>(e1), forward<T2>(e2));
}
```

下面是`forward`的实现[^3]:

``` C++
template<class T>
T&& forward(typename std::remove_reference<T>::type& t) noexcept {
  return static_cast<T&&>(t);
}
```

假设我们这样调用：

``` C++
int ii ...;
float ff ...;
wrapper(ii, ff);
```

我们来分析第一个参数是怎么传递的（第二个参数也类似）：ii是一个左值，根据推导规则，T1被推导为`int&`，此时函数调用为`func(forward<int&>(e1), ...)`，从而，`forward`函数使用`int&`具现化，那么具现化后的函数为：

``` C++
int& && forward(int& t) noexcept {
    return static_cast<int& &&>(t);
}
```

然后应用引用折叠规则：

``` C++
int& forward(int& t) noexcept {
    return static_cast<int&>(t);
}
```

也就是说，参数是以传引用方式传入func函数，与我们对左值参数的预期一致。

再来考虑另外一种情况：

``` C++
wrapper(42, 3.14f);
```

此时参数为右值，所以T1推导为`int`，具体的函数调用为`func(forward<int>(e1), ...)`，因此`forward`函数以`int`进行具现化，最终的函数为：

``` C++
int&& forward(int& t) noexcept {
    return static_cast<int&&>(t);
}
```

此时引用参数被转换为右值引用，与我们的预期一致。

`forward`函数是`static_cast<T&&>(t)`表达式的简单封装，根据wrapper的参数类型为左值或者右值，T被推导为U&或者U&&。使用一个wrapper模板函数可以清晰地处理所有类型的参数传递。

`forward`模板函数已经加入到C++11中，位于`<utility>`头文件中，模板函数名为`std::forward`。

此外`std::remove_reference<T>`也有必要介绍一下。事实上，仔细想想，`forward`函数不需要它也能正常工作。引用折叠规则已经达到了`std::remove_reference`的效果，所以此处`std::remove_reference<T>`是多余的。它的功能是将`T& t`导入一个没有类型推导的语境中（参考C++标准，14.8.2.5节），从而强制要求程序员在调用`std::forward`时显式指定模板参数。

# 通用引用[^4]

Scott Myers在他的演讲、博客和专著中将这种在类型推导语境中使用的右值引用称为“通用引用”。到底这个助记符有没有用取决于具体的人。对于我个人而言，当我第一次阅读"Effectve Modern C++"的相关章节时，我被这个主题弄糊涂了。直到我逐渐理解了底层工作机制（即引用折叠和特殊推导规则）之后，相关主题才变得清晰起来。

使用“通用引用”这个名字确实比“类型推导语境中的右值引用”更简练更好，但是如果需要真正理解某些代码而不是简单的依样画葫芦的话，还是需要弄清楚这个概念的完整定义。

# 完美传递的实际例子

完美传递非常有用，因为它打开了一扇通往高阶函数编程的大门。那些需要以函数作为参数或者返回值的函数称为高阶函数。如果没有完美传递这个特性，高阶函数的实现就非常累赘，因为缺少一种向封装的函数传递参数的便捷方式。此处我们提到的“函数”其实也包括类，因为类的构造函数也是一种函数。

在本文的开始，我介绍了容器类的`emplace_back`方法。此外还有一个使用完美传递的函数就是`make_unique`：

``` C++
template<typename T, typename... Args>
unique_ptr<T> make_unique(Args&&... args)
{
	return unique_ptr<T>(new T(std::forward<Args>(args)...));
}
```

之前我略过了对奇怪的`&&`语法的介绍，集中介绍可变参数模板，但是在本文中我们可以毫无压力地理解这段代码了。完美传递和可变参数模板通常配合使用，因为我们通常并不知道函数或构造函数的参数个数是多少。

# 相关资源链接

我在写本文时发现这些资源非常有帮助：

* 《The C++ Programming Language》第4版，Bjarne Stroustrup
* 《Effective Modern C++》，Scott Myers详细介绍了“通用引用”这个概念，事实上，全书超过1/5的内容都在讨论这个主题！
* [n1385: "The forwarding problem: Arguments"](http://www.open-std.org/jtc1/sc22/wg21/docs/papers/2002/n1385.htm)
* [C++ Rvalue references explained](http://thbecker.net/articles/rvalue_references/section_01.html)写得非常好，也非常有用

[^1]: 
此规则也适用于其它情况，如`auto`和`decltype`。在此之介绍模板的情况。

[^2]:
我认为C++委员会应该为这种情况选用不同的语法，从而与&&语法区分开来。注意到这种语法并不常用，所以为此修改语言的语法并不值得（C++委员会一贯尽量避免这种修改），但是窃以为现在的情况太混乱了。即使如Scott Myers这种大牛也在演讲和博客评论中承认，即使已经过了3年，这些材料依然还太复杂。Bjarne Stroustrup在《The C++ Programming Language》一书中介绍`std::forward`时也犯了一个错误：调用`std::forward`时忘记显式提供模板参数。这有点太复杂了！

[^3]:
这是C++11中的std::forward函数的一个简化版本。

[^4]:
在其它地方也称为“传递引用”