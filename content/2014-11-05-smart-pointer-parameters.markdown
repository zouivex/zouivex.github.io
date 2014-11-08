Title: GotW-91 智能指针参数
Slug: smart-pointer-parameters
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

`shared_ptr`内部存有强引用计数和弱引用计数（参见[GotW #89]()）。若以传值方式传递，那么通常在函数的入口处对传入参数进行复制，然后在函数出口处销毁。让我们对此进行详细剖析。

在函数入口处，参数`shared_ptr`被拷贝构造，同时还需要递增强引用计数。（是的，如果调用函数传入的是一个临时的`shared_ptr`，只需进行移动构造从而无需修改引用计数。但是，(a)在一般代码中使用临时`shared_ptr`的情况很少，一般都是将函数的返回值立即传递给另一个函数；(b)而且我们将看到函数的性能开销主要耗费在参数的销毁上。）

在函数的出口处，`shared_ptr`参数被销毁，此时需要递减内部的引用计数。

递增和递减递减共享的引用计数有什么不好的方面呢？两方面，其一与”共享的引用计数“相关，其二与”递增和递减引用计数“相关。弄明白引用计数对性能造成影响的两个原因对我们非常有好处：其中一个是主要并且普遍的原因，另一个不大可能出现在设计良好的代码中，故而相对次要。

第一，递增递减操作导致的性能开销是一个主要的原因：因为引用计数是一个共享的原子变量（或类似的变量），对其进行递增递减在内部其实是进行同步的"读-修改-写"模式的内存操作。

第二，另一个相对次要的原因是”共享引用计数“在进行大规模扩展时会发生争用：递增和递减操作都会更新引用计数，即是说在处理器和内存层面同一时刻只有一个CPU核能在同一个引用计数变量上执行指令，因为此操作需要对引用计数所在的cache行进行独占的访问。其结果是在访问引用计数的cache行时会发生争用，例如在密集的循环中，多个线程同时访问同一个cache行，此时会严重影响可扩展性，例如两个线程在密集循环中调用类似的函数，并且同时访问指向同一个共享对象的`shared_ptr`。所以我们要大声疾呼，”用户们，请不要这样使用！“。其它都好说，只是并不是所有用户都知道两个线程中不同的两个`shared_ptr`其实指向的是同一个对象，所以我们在此先不着急深入讨论此问题。

我们会看到，对于所有基于引用计数的智能指针都有一个基本的最佳实践，那就是避免进行拷贝，除非确实需要增加一个引用。这直接避免了上面介绍的两种影响性能的因素，从而大大降低了它们对大部分程序性能的影响，特别是第二种因素，因为在密集循环中添加、移除引用是一种“反模式”。

此时此刻，我们会想到采用传引用的方式传递`shared_ptr`也许能解决上面的问题。但是这真的是一个正确的解决方案吗？还是要具体情况具体分析。

## 上面的函数声明的正确性如何？请举例解释你的答案。

在正确性上唯一的好处是函数清晰地、以类型强制的方式表明了函数将要（或者能够）复制一个`shared_ptr`对象。

这是唯一正确之处可能让很多人吃惊，因为看起来复制参数还有一个非常重要的好处，即生命期管理，假设当前`shared_ptr`指针非空，对其进行拷贝能够保证参数本身持有对象的一个强引用，因此能够保证该对象在函数体的执行期间一直存在，直到函数自己决定修改其参数。

但是，上面提到的特性不需要复制参数也能满足，这归功于结构化生命期管理，被调用函数的生命期是调用表达式生命期的一个严格子集。就算我们通过传引用传递`shared_ptr`，其效果和持有参数的强引用一样，因为调用函数已经持有一个强引用了（`shared_ptr`作为参数传入函数，直到函数返回之后才释放引用）。注意：我们在此假设指针没有别名，必须小心智能指针参数别名引发的问题，但是它和其他类型的对象由于别名导致的问题是一样的。

> 准则：通过传值、*、&的方式传递对象参数，而不要通过智能指针，除非你就是想要操作智能指针本身，例如共享或者转移所有权。

如果你要问：“难道裸指针没有弊端吗？”，非常好，我们在下面一节会讨论这个问题。

## 此处列出的智能指针参数使用方法都在什么情况下适用？

### (a)和(b) 以指针或者引用的方式传递参数

``` C++
void f( widget* );              (a)
void f( widget& );              (b)
```

这是传递普通对象参数的推荐方式，因为这种方式可以不用了解调用函数所采用的生命期管理策略。

可以使用非占用性的裸指针和引用来指向生命期超出指针或者引用生命期的对象，将它们作为参数传递时的就是这种情况。由于结构化生命期管理，在默认情况下，传递给函数f的参数比f的调用生命期长，这对于将非占用性的指针和引用作为合适的参数类型非常有用（更别提非常有效率了）。

通过指针或者引用传入一个widget对象，与调用函数如何管理对象的生命期是独立开的。大部分情况下，我们不希望绑定到单一的生命期管理策略，例如要求对象必须使用某种特定的智能指针才能使用，因为这种限制通常是不必要的。一般来说，如果希望表达空（即无widget）的概念时，使用指针，其他情况推荐使用引用，如果对象只作为输入，那么加上`const`，写成`const widget*`或者`const widget&`。

### (c) 按值传递`unique_ptr`表达sink语义
``` C++
void f( unique_ptr<widget> );   (c)
```

这种方式表达的意思是：函数需要使用widget对象，即"sink"。

按值传递`unique_ptr`将对象及其所有权从调用者转移给被调用者。和(c)类似的函数会将对象的所有权从调用者转移走，要么将对象销毁，要么将对象继续传递到其他地方。

注意，与下面几种方式不同的是，按值传递`unique_ptr`实际上并没有限制传入的对象的类型。原因为何？因为任何指针类型都可以显式地转换为`unique_ptr`。如果我们在此不使用`unique_ptr`，我们还是得表达"sink"语义，只不过必须采用更脆弱的方式，比如使用占用性的裸指针（真可怕！），或者在注释中描述此语义。使用(c)方式要更好，因为这样在代码中表达了语义，并且要求调用者显式地转移对象的所有权。

请思考此方式的主要替代方式：

``` C++
// Smelly 20th-century alternative
void bad_sink( widget* p );  // will destroy p; PLEASE READ THIS COMMENT

// Sweet self-documenting self-enforcing modern version (c)
void good_sink( unique_ptr<widget> p );
```

可以看到(c)方式要好很多：

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

> 准则：按值传递`unique_ptr`参数，表达sink语义。

因为被调函数将拥有对象的所有权，所以通常参数没有const限定，此处使用const就不恰当了。

### (d) 按引用传递`unique_ptr`是为了传入、传出`uniue_ptr`类型的参数

``` C++
void f( unique_ptr<widget>& );  (d)
```

这种方式只适用于将`unique_ptr`作为输入、输出参数使用的情况，此时函数传入一个`unique_ptr`并且有可能将其修改为指向不同的对象。如果只需要传入一个widget对象，那么使用这种方式就不是很好了，因为这样对调用函数的生命期管理方式作了严格的限制。

> 准则：non-const的`unique_ptr&`参数只适合使用在需要修改`unique_ptr`的场合。

传入`const unique_ptr<widget>&`参数非常奇怪，因为这样函数只能传入空指针或者widget对象，此对象的生命期已经在调用代码中通过`unique_ptr`的方式进行了管理，但是通常来说被调函数不应该关心调用函数的生命期管理策略。传入`widget*`已经覆盖了这些情况，无论调用函数采用的是什么生命期管理策略，都可以传入空指针或者widget对象。

> 准则：不要使用`const unique_ptr<widget>&`类型的参数，使用`widget*`类型。

此处采用`widget*`的原因是它没有改变对象可以为空的语义。如果你动了使用`const shared_ptr<widget>&`的心思，那么其实和使用`widget*`表达的是同样的意思。如果还知道对象不可能为空，那么当然应该使用`widget&`。

### (e) 按值传递`shared_ptr`表明共享所有权

``` C++
void f( shared_ptr<widget> );   (e)
```

第2节中提到，只有当函数的意图是持有`shared_ptr`的拷贝并且共享对象的所有权时才推荐这样使用。此时，无论如何需要复制一份`shared_ptr`，因此复制的开销尚可以接受。如果局部作用域还不是最终的目的地，那么使用`std::move`将`shared_ptr`转移到目的对象即可。

> 准则：按值传递`shared_ptr`，表示函数将要存储并且持有对象的共享所有权。

其他情况下，请使用裸指针和引用传递参数，因为这样避免函数将传入参数的类型限制为`shared_ptr`。

### (f) 按引用传递`shared_ptr`对于传入、传出`shared_ptr`类型的参数非常有用
``` C++
void f( shared_ptr<widget>& );  (f)
```

与(d)类似，这种方式主要适用于传入、传出`shared_ptr`类型参数时，此时函数预计会对传入的`shared_ptr`指针本身进行修改。这种方式不适用于需要传入widget对象的情况，因为这样会对调用函数的生命期管理策略作出限制。

如(e)中所说，只有当需要共享所有权时才按值传递`shared_ptr`参数。在某些特殊情况下，函数可能需要共享所有权，但是并不需要将参数进行复制，此时传递`const shared_ptr&`类型的参数，这样调用函数能够酌情对参数进行复制。

> 准则：只在需要修改`shared_ptr`时传入非const的`shared_ptr&`参数。只有当你不清楚是否需要进行复制并且共享所有权时才使用`const shared_ptr&`参数，否则使用`widget*`类型的参数（如果确信对象不能为空，那么使用`widget&`）。

