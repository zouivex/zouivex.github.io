Title: 介绍一种广泛使用的git workflow
Slug: a-successful-git-branching-model
Date: 2014-10-24 22:14:17
Modified: 2014-10-24 22:14:17
Category: 译文
Tags: git, tools

[TOC]

本文展示了一种工作流模型，此模型从一年前就开始在我所有项目（工作项目和私人项目）中非常成功地采用。
我早就想写一篇介绍文章，但是直到现在才抽出时间完整写出本文。本文不会深入描述具体项目的细节，
仅仅介绍branch的策略和发布管理。

![git branch model]({filename}/images/git-model.png)

下面集中介绍如何采用Git作为源代码的版本管理工具。

# 为何使用git?

Git和那些集中式源代码管理系统相比其优势和劣势请参看此[网页](http://git.or.cz/gitwiki/GitSvnComparsion)。
关于这个问题有很多论战。作为开发人员，我认为当前Git比其它工具都要优秀。Git确确实实改变了开发人员merge和branch的思考方式。
在之前CVS/Subversion的时代，merge/branch一直以来都被认为是件可怕的事情（“前方merge冲突伤人，请勿靠近！”）因此不能随便进行。

相反，在Git中merge/branch资源消耗少同时非常简单，因此被认为是日常工作流程的核心一环，而且事实确实如此。
例如，在CVS/Subversion[书籍](http://svnbook.red-bean.com/)中，merge和branch在靠后的章节介绍（面向高级用户），
但是在Git[书籍](http://pragprog.com/titles/tsgit/pragmatic-version-control-using-git)中，
在第三章就开始介绍merge和branch（被认为是基础功能）。

由于merge和branch非常简单并且可以重复进行，因此再也不会让人像以前（在Subversion时代）那样感到恐惧。
版本控制工具理所应当为merge/branch操作提供比其他工具强大的功能。

对工具进行介绍之后，让我们开始介绍开发工作模型。下面要介绍的工作模型是项目组所有成员进行软件开发过程管理所采取的工作流程的集合。

# 逻辑上中央式，物理上分布式

我们在本文中使用的源码库包含一个名为trunk的中央库。注意，此中央库只不过在（逻辑上）被看作中央库
（由于Git是一个分布式版本管理系统，因此从技术上来说不存在中央库这个概念）。
由于`origin`这个名字对于所有Git用户来说都很熟悉，此后我们称逻辑中央库为`origin`。

![center-decenter]({filename}/images/center-decenter.png)

开发者一般情况下是对`origin`库进行pull和push操作。但是在需要分布式的操作时，开发者可以从其它开发者处pull修改后的代码，这样构成开发子小组。
例如，有时候需要和2个以上的开发人员配合工作以完成一个较大的功能，等开发成熟之后再将代码push到`origin`库。
上面的流程图中，Alice和Bob、Alice和David、Clair和David分别组成开发子小组。

在技术层面上，其实就是Alice定义一个名为bob的Git远程库以指向Bob的本地库，反之亦然。

# 主要branch

本文介绍的开发模型依然与现有的开发模型一脉相承。其中心代码库有两个永久保存的branch：

* `master`
* `develop`

`origin`库的`master`branch对于Git用户来说非常熟悉，除此之外`origin`库还有一个`develop`branch。

![main-branches]({filename}/images/main-branches.png)

`origin/master`branch是源代码库的主branch，其HEAD版本总是反映源代码可以发布的状态。

`origin/develop`branch作为源代码的开发branch，其HEAD反映的是最新的可提交到下一版本的代码修改，所以我们称之为“集成branch”。每日自动构建总是在此branch进行。

当`develop`branch中的代码达到稳定状态并且准备好发布的时候，其中的所有修改都应该merge回`master`branch，并且tag一个发布版本号。具体操作在之后会进行讨论。

因此，每次代码修改merge回`master`branch时，从定义上来说就是一个新的版本。我们倾向于严格执行merge回`master`branch的操作，因此理论上来说每次提交代码到`master`branch时，我们都可以使用Git hook脚本自动构建并且发布新版本。

# 辅助branch

除了主要branch`master`和`develop`之外，我们的开发模型还使用辅助branch来支持成员之间的并行开发、跟踪开发中的功能、准备版本发布以及帮助快速修复生产环境中的问题。
与主要branch不同，辅助branch的生命周期比较短，因为它们最终会被删除。

我们有以下不同种类的辅助branch可以使用：

* 功能branch
* 发布branch
* 快速修复branch

以上的不同branch都有其特定的用途，关于哪些branch是源branch、哪些是merge的目标branch有其严格的规则。之后我们会详细介绍这些规则。

但是在技术层面上，这些branch都没有什么特别的，对它们的分类是基于我们如何使用它们，本质上它们都不过是简单的Git branch。

## 功能branch

* 功能branch从以下branch创建：
: `develop`
* 功能branch必须merge回以下branch：
: `develop`
* 功能branch的命名规则：
: 除了`master`，`develop`，`release-*`，和`hotfix-*`之外的所有名字

![feature-branches]({filename}/images/feature-branches.png)

功能branch（也称为主题branch）用于开发下一版本或者将来版本中的功能。开始在功能branch中开发新功能时，集成此新功能的目标发布版本还未知。功能branch的精髓在于：
只要功能还未开发完成，功能branch就一直存在，但是最终要么被merge回`develop`branch（此时为下一个发布版本添加新功能），要么被丢弃（若功能的测试结果不太令人满意）。

功能branch通常只存在于开发人员的本地库，而不存在于`origin`库。

### 创建功能branch

当开始开发新功能时，从`develop`branch创建新的功能branch：

```
$ git checkout -b myfeature develop
Switched to a new branch "myfeature"
```

### 功能完成后集成回`develop`branch

功能开发完成后，功能branch需要merge回`develop`branch，并将它们加入下一个发布版本：

```
$ git checkout develop
Switched to branch 'develop'
$ git merge --no-ff myfeature
Updating ea1b82a..05e9557
(Summary of changes)
$ git branch -d myfeature
Deleted branch myfeature (was 05e9557).
$ git push origin develop
```

`--no-ff`选项的意思是对branch进行merge时总是创建新的提交对象，不管此时是不是可以只通过`fast-forward`merge就能完成。
这样可以避免丢失该功能branch存在的历史信息，同时还能将此功能相关所的有提交组合起来。请参看下图的比较：

![merge-without-ff]({filename}/images/merge-without-ff.png)

上图的后一种情况下，不可能从Git历史日志中分辨出哪些commit实现了某个功能，必须人工阅读所有的Git日志才行。
如果想要revert某个功能（若包含多个commit），用后一种方法实在不容易完成，而用`--no-ff`选项则非常容易。

确实，这样会创建一些空commit，但是所得的回报比付出要大得多。

不幸的是，我还没有发现能够将`--no-ff`设置为`git merge`的默认选项的方法，但是窃以为`--no-ff`确实应该设置为默认选项。

## 发布branch

* 发布branch从以下branch创建：
: `develop`
* 发布branch必须merge回以下branch：
: `develop`
: `master`
* 发布branch的命名规则：
: `release-*`

发布branch用于支持新版本的发布准备，它允许最后时刻的小修改。此外还允许修复小bug以及准备新版本的元数据（版本号、构建时间、等等）。
所有的工作都在发布版本中完成，此时不再允许提交下一版本功能相关的代码到`develop`branch。

从`develop`branch创建发布branch的关键点是：`develop`branch需要（几乎）达到了下一个版本所期望的状态。此刻，即将发布的版本所包含的所有功能都必须merge回`develop`branch。
而未来版本中的功能不用merge回`develop`branch，因为必须等到发布branch创建之后才能merge。

在发布branch创建之时才能决定下一个版本的版本号。此时`develop`branch能够反映下一个版本中的所有修改，但是依然还不清楚下一个版本最终会是0.3还是0.1。
所以需要在创建发布branch时，根据项目的版本号分配规则决定下一个版本号。

### 创建发布branch

发布branch从`develop`branch创建而来。例如，当前生产版本为1.1.5，如果马上有一个大的版本发布，`develop`branch中下一个版本的所有修改已经完成，
我们决定下一个版本号为1.2（不是1.1.6或2.0），则我们创建一个发布branch并且命名为下一个即将发布的版本号：

```
$ git checkout -b release-1.2 develop
Switched to a new branch "release-1.2"
$ ./bump-version.sh 1.2
Files modified successfully, version bumped to 1.2.
$ git commit -a -m "Bumped version number to 1.2"
[release-1.2 74d9424] Bumped version number to 1.2
1 files changed, 1 insertions(+), 1 deletions(-)
```

创建新发布branch并切换到新branch之后，需要替换版本号。在此，`bump-version.sh`是一个假想的脚本，
用来替换工作拷贝中某些文件的版本号（也可以手动替换文件中的版本号）。替换版本号之后，提交代码。

发布branch可能存在一段时间，直到版本最终发布出去为止。在此期间，修复bug的代码可能提交到此branch（而不是`develop`branch）。
严格禁止在发布branch中添加新功能，新功能必须merge回`develop`branch，并包含在下一版本中。

### 结束发布branch

当发布branch中的代码准备好发布时，需要采取一些行动。首先，merge发布branch到`master`branch（记住，任何一次到`master`branch的提交都是一个新的版本）。
其次，这些到`master`branch的commit必须打上tag以便于在将来通过历史版本引用。最后，发布branch中的改动需要merge回`develop`branch，确保新发布的版本包含这些修改。

下面是前两个步骤的Git命令：
```
$ git checkout master
Switched to branch 'master'
$ git merge --no-ff release-1.2
Merge made by recursive.
(Summary of changes)
$ git tag -a 1.2
```

此刻发布完成，并且作好tag以便将来引用。

发布版本中的修改需要merge回`develop`branch，Git命令为：

```
$ git checkout develop
Switched to branch 'develop'
$ git merge --no-ff release-1.2
Merge made by recursive.
(Summary of changes)
```

此时进行merge发生冲突还可以接受（其实只是有可能产生冲突，因为我们修改了版本号）。如果发生冲突，解决冲突并commit。

现在新版本的发布真的完成了，发布branch功成身退，因为我们不再需要了：

```
$ git branch -d release-1.2
Deleted branch release-1.2 (was ff452fe).
```

## 快速修复branch

* 快速修复branch从以下branch创建：
: `master`
* 快速修复branch必须merge回branch：
: `develop`
: `master`
* 快速修复branch的命名规则：
: `hotfix-*`

![hotfix-branches]({filename}/images/hotfix-branches.png)

快速修复branch与发布branch非常相似，其存在也是为了支持新版本的发布准备，只不过它是有计划的。
当生产机上运行的版本出现未知问题时，可以使用快速修复branch来解决。
当生产版本发生急需解决的严重问题时，可以从`master`branch中对应的tag版本创建快速修复branch。

此处的要点是工作在`develop`branch的项目组成员可以继续工作，而其他人可以同时准备一个针对生产版本的快速修改。

### 创建快速修复branch

快速修复branch从`master`branch创建而来。例如当前正在运行生产系统版本为1.2，由于一个bug导致系统问题。
但是此时`develop`branch中的修改还不稳定，我们可以创建一个快速修复branch来修复此问题：

```
$ git checkout -b hotfix-1.2.1 master
Switched to a new branch "hotfix-1.2.1"
$ ./bump-version.sh 1.2.1
Files modified successfully, version bumped to 1.2.1.
$ git commit -a -m "Bumped version number to 1.2.1"
[hotfix-1.2.1 41e61bb] Bumped version number to 1.2.1
1 files changed, 1 insertions(+), 1 deletions(-)
```

别忘了在创建branch时替换版本号。然后，修复bug并且分一次或多次提交修复：

```
$ git commit -m "Fixed severe production problem"
[hotfix-1.2.1 abbe5d6] Fixed severe production problem
5 files changed, 32 insertions(+), 17 deletions(-)
```

### 结束快速修复branch

修复完成之后，代码修改需要merge回`master`branch，同时还需要merge回`develop`branch，这样确保代码修改同时也被包含到下一个发布版本。
这与完成发布branch的方式类似。

首先，更新`master`branch并且tag版本号。

```
$ git checkout master
Switched to branch 'master'
$ git merge --no-ff hotfix-1.2.1
Merge made by recursive.
(Summary of changes)
$ git tag -a 1.2.1
```

接着，将所有修改也merge到`develop`branch：

```
$ git checkout develop
Switched to branch 'develop'
$ git merge --no-ff hotfix-1.2.1
Merge made by recursive.
(Summary of changes)
```

也有一个例外，当存在发布branch时，快速修复branch中的修改需要merge回发布branch而不是`develop`branch。
将代码修改merge回发布branch，这样在发布branch完成之后代码修改最终自然会merge回`develop`branch。
如果`develop`branch急切需要这些修改，等不到发布branch完成，也可以同时安全地merge这些代码改动到`develop`branch。

最后，删除临时的快速修复branch：

```
$ git branch -d hotfix-1.2.1
Deleted branch hotfix-1.2.1 (was abbe5d6).
```

# 总结

本文开始处引用的"全图"虽然与本文描述的branch模型相比没有太大差别，但是它在我们的项目中非常有用。
此图展示了一种优美的思维模型，非常易于理解，并且让项目组成员之间对branch和发布流程产生相同的理解。

[此处](http://nvie.com/files/Git-branching-model.pdf)提供有高质量的PDF版本，请将其打印出来并挂到公司的墙壁上以便时时参考。

# 翻译说明

本文为翻译文章，此为[原文链接](http://nvie.com/posts/a-successful-git-branching-model)。
