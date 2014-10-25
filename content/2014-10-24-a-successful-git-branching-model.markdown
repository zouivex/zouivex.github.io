Title: 一种成功的git分支模型
Slug: a-successful-git-branching-model
Date: 2014-10-24 22:14:17
Modified: 2014-10-24 22:14:17
Category: 译文
Tags: git, tools

[TOC]

本文展示了一种开发模型，此模型从一年前就开始在我所有项目（工作项目和私人项目）中非常成功地采用。我早就想写一篇介绍文章，但是直到现在才抽出时间从头到尾写出本文。本文不会深入描述具体项目的细节，仅仅介绍分支策略和发布管理。

![git branch model]({filename}/images/git-model.png)

下面集中介绍如何采用Git作为源代码的版本管理工具。

# 为何使用git?

Git和那些集中式源代码管理系统相比其优势和劣势请参看此[网页](http://git.or.cz/gitwiki/GitSvnComparsion)。关于这个问题有很多论战。作为开发人员，我认为当前Git比其它工具都要优秀。Git确确实实改变了开发人员合并和分支的思考方式。在之前CVS/Subversion的时代，合并/分支一直以来都被认为是件可怕的事情（“前方合并冲突伤人，请勿靠近！”）因此需要节制进行。

相反，在Git中合并/分支非常廉价和简单，因此被认为是日常工作流程的核心一环，而且事实确实如此。例如，在此CVS/Subversion[书籍](http://svnbook.red-bean.com/)中，分支和合并在后面的章节介绍（面向高级用户），但是在此Git[书籍](http://pragprog.com/titles/tsgit/pragmatic-version-control-using-git)中，在第三章就开始介绍分支和合并（被认为是基础功能）。

由于分支和合并非常简单并且可以重复进行，因此再也不像以前那样令人害怕。版本控制工具应当比其它工具更能帮助开发者进行分支/合并操作。

对工具进行介绍之后，让我们开始介绍开发模型。下面要介绍的模型不过是项目组所有成员进行软件开发过程管理所采取的工作流程的集合。

# 物理去中心化，逻辑中心化

我们在例子中使用的与分支模型工作良好的源码库包含一个名为truth的中央库。注意，此中央库只不过是（逻辑上）被看作中央库（由于Git是一个分布式版本管理系统，因此从技术上来说不存在中央库这个概念）。由于`origin`这个名字对于所有Git用户来说都很熟悉，此后我们称逻辑中央库为`origin`。

![center-decenter]({filename}/images/center-decenter.png)

开发者一般情况下对`origin`库进行pull和push操作。但是在需要非中心化的操作时，开发者可以从其它开发者处pull修改后的代码，这样构成开发子小组。例如，有时候需要和2个以上的开发人员配合工作以完成一个较大的功能，等开发成熟之后再将代码push到`origin`库。上面的流程图中，Alice和Bob、Alice和David、Clair和David分别组成开发子小组。

技术上讲，是Alice定义一个名为bob的Git远程库以指向Bob的本地库，反之亦然。

# 主要分支

开发模型的核心受现有模型的启发。中心代码库有两个永久保存的分支：

* `master`
* `develop`

Git用户对`origin`库的`master`分支很熟悉，同时还有一个`develop`分支与`master`分支同时存在于`origin`库中。

![main-branches]({filename}/images/main-branches.png)

`origin/master`分支是源代码库的主分支，其HEAD版本总是反映源代码可以发布的状态。

`origin/develop`分支作为源代码的开发分支，其HEAD反映的是最新的可提交到下一版本的代码修改的状态，所以我们称之为“集成分支”。每日自动构建总是在此分支进行。

当`develop`分支中的代码达到稳定状态并且准备好发布的时候，其中的所有修改都应该合并回`master`分支，并且标记一个发布版本号。具体操作在之后会进行讨论。

因此，每次代码修改合并回`master`分支时，从定义上来说就是一个新的版本。我们倾向于严谨执行合并回`master`分支的操作，因此理论上来说每次提交代码到`master`分支时，我们都可以使用Git hook脚本自动构建并且部署新版本到生产服务器。

# 辅助分支

除了主要分支`master`和`develop`之外，我们的开发模型还使用辅助分支来支持成员之间的并行开发、跟踪开发的功能、准备版本发布以及帮助快速修复生产环境中的问题。与主要分支不同，辅助分支的生命周期比较短，因为它们最终会被删除。

我们有以下不同种类的辅助分支可以使用：

* 功能分支
* 发布分支
* 热修复分支

以上的不同分支都有其特定的用途，关于哪些分支是源分支、哪些是合并分支有其严格的规则。之后我们会详细介绍这些规则。

但是从技术层面来说，这些分支都没有什么特别的，对它们如何分类是基于我们如何使用它们。本质上它们都不过是简单的Git分支。

## 功能分支

* 功能分支从以下分支创建：
: `develop`
* 功能分支必须合并回分支：
: `develop`
* 功能分支的命名规则：
: 除了`master`，`develop`，`release-*`，和`hotfix-*`之外的所有名字

![feature-branches]({filename}/images/feature-branches.png)

功能分支（也称为主题分支）用于开发即将发布或者将来发布的版本中的功能。当开始开发新功能时，要集成此功能的目标发布版本还未知。功能分支的精髓在于：只要功能还未开发完成，功能分支就一直存在，但是最终要么被合并回`develop`分支（此时为下一个发布版本添加新功能），要么被丢弃（试验结果不令人满意）。

功能分支通常只存在于开发库，而不存在于`origin`库。

### 创建功能分支

当开始开发新功能时，从`develop`分支创建新的功能分支：

``` 
$ git checkout -b myfeature develop
Switched to a new branch "myfeature"
```

### 功能完成后集成回`develop`分支

功能开发完成后，将功能分支合并回`develop`分支，并将它们加入下一个发布版本：

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

`--no-ff`选项的意思是在合并分支时总是创建新的提交对象，即使此时可以只通过`fast-forward`合并就能完成。这样可以避免丢失该功能分支存在的历史信息，同时将此功能相关所有提交组合起来。请参看下图的比较：

![merge-without-ff]({filename}/images/merge-without-ff.png)

上图的后一种情况下，不可能从Git历史日志中看出哪些提交对象实现了某个功能，必须人工阅读所有的Git日志才行。如果想要回滚某个功能（包含一组提交），用后一种方法真的不容易完成，而用`--no-ff`选项非常容易完成。

确实，这样会创建一些空提交对象，但是所得的回报比付出要大得多。

不幸的是，我还没有发现能够将`--no-ff`设置为`git merge`的默认选项的方法，但是`--no-ff`确实应该设置为默认选项。

## 发布分支

* 发布分支从以下分支创建：
: `develop`
* 发布分支必须合并回分支：
: `develop`和`master`
* 发布分支的命名规则：
: `release-*`

发布分支用于支持新版本的发布准备，它允许最后时刻的小修改。此外还允许修复小bug以及准备新版本的元数据（版本号、构建时间、等等）。所有的工作都在发布版本中完成，此时`develop`分支不再允许提交与下一个大版本的新功能相关的代码。

从`develop`分支创建发布分支的关键点是：`develop`分支需要（几乎）达到了下一个版本所期望的状态。此刻，即将发布的版本所包含的所有功能都必须合并回`develop`分支。而将来才发布的版本中的功能不用合并回`develop`分支，因为它们必须等到发布分支创建之后。

在发布分支创建之时才能决定下一个版本的版本号。此时`develop`分支反映下一个版本中的所有修改，但是依然还不清除下一个版本最终会是0.3还是0.1。在创建发布分支时，根据项目的版本号分配规则决定下一个版本号。

### 创建发布分支

发布分支从`develop`分支创建而来。例如，当前生产版本为1.1.5，马上就有一个大的版本发布。`develop`分支为下一个版本的所有修改已经完成，我们决定下一个版本号为1.2（不是1.1.6或2.0）。所以我们创建一个发布分支并且命名为下一个即将发布的版本号：

```
$ git checkout -b release-1.2 develop
Switched to a new branch "release-1.2"
$ ./bump-version.sh 1.2
Files modified successfully, version bumped to 1.2.
$ git commit -a -m "Bumped version number to 1.2"
[release-1.2 74d9424] Bumped version number to 1.2
1 files changed, 1 insertions(+), 1 deletions(-)
```

创建新发布分支并切换到新分支之后，需要替换版本号。在此，`bump-version.sh`是一个假想的脚本，用来替换工作拷贝中某些文件的版本号（也可以手动替换文件中的版本号）。替换版本号之后，提交代码。

发布分支可能存在一段时间，直到版本最终发布出去为止。在此期间，修复bug的代码可能提交到此分支（而不是`develop`分支）。严格禁止在发布分支中添加新功能，新功能必须合并回`develop`分支，并包含在下一版本中。

### 完成发布分支

当发布分支中的代码准备好发布时，需要采取一些行动。首先，将发布分支合并到`master`分支（记住，任何一次到`master`分支的提交都是一个新的版本）。其次，这些到`master`分支的提交必须打上标记以便于在将来通过历史版本引用。最后，发布分支中的改动需要合并回`develop`分支，确保新发布的版本包含这些修改。

前两个步骤在Git中的命令：
```
$ git checkout master
Switched to branch 'master'
$ git merge --no-ff release-1.2
Merge made by recursive.
(Summary of changes)
$ git tag -a 1.2
```

此刻发布完成，并且作好标记便将来引用。

发布版本中的修改需要合并回`develop`分支，Git命令为：

```
$ git checkout develop
Switched to branch 'develop'
$ git merge --no-ff release-1.2
Merge made by recursive.
(Summary of changes)
```

此时产生合并冲突没有什么大问题（只是有可能产生冲突，因为我们修改了版本号）。如果产生冲突，解决冲突并提交。

现在真的完成新版本的发布，此时发布分支功成身退，因为我们不再需要它们了：

```
$ git branch -d release-1.2
Deleted branch release-1.2 (was ff452fe).
```

## 热修复分支

* 热修复分支从以下分支创建：
: `master`
* 热修复分支必须合并回分支：
: `develop`和`master`
* 热修复分支的命名规则：
: `hotfix-*`

![hotfix-branches]({filename}/images/hotfix-branches.png)

热修复分支与发布分支非常相似，其存在也是为了支持新版本的发布准备，只不过它是有计划的。当生产线上运行的版本出现未知问题时，可以采用热修复分支来解决。当生产版本发生急需解决的严重问题时，可以从`master`分支中对应的标记版本创建热修复分支。

此处的要点是工作在`develop`分支的项目组成员可以继续工作，而其他人可以同时准备一个针对生产版本的快速修改。

### 创建热修复分支

热修复分支从`master`分支创建而来。例如当前正在运行生产系统版本为1.2，由于一个bug导致系统问题。但是此时`develop`分支中的修改还不稳定，我们可以创建一个热修复分支来修复此问题：

```
$ git checkout -b hotfix-1.2.1 master
Switched to a new branch "hotfix-1.2.1"
$ ./bump-version.sh 1.2.1
Files modified successfully, version bumped to 1.2.1.
$ git commit -a -m "Bumped version number to 1.2.1"
[hotfix-1.2.1 41e61bb] Bumped version number to 1.2.1
1 files changed, 1 insertions(+), 1 deletions(-)
```

别忘了在创建分支时替换版本号。然后，修复bug并且分一次或多次提交修复：

```
$ git commit -m "Fixed severe production problem"
[hotfix-1.2.1 abbe5d6] Fixed severe production problem
5 files changed, 32 insertions(+), 17 deletions(-)
```

### 完成热修复分支

修复完成之后，代码修改需要合并回`master`分支，同时还需要合并回`develop`分支，这样确保代码修改同时也被包含到下一个发布版本。这与完成发布分支的方式类似。

首先，更新`master`分支并且标记版本号。

```
$ git checkout master
Switched to branch 'master'
$ git merge --no-ff hotfix-1.2.1
Merge made by recursive.
(Summary of changes)
$ git tag -a 1.2.1
```

接着，将所有修改也合并到`develop`分支：

```
$ git checkout develop
Switched to branch 'develop'
$ git merge --no-ff hotfix-1.2.1
Merge made by recursive.
(Summary of changes)
```

也有一个例外，当存在发布分支时，热修复分支中的修改需要合并回发布分支而不是`develop`分支。将代码修改合并回发布分支，这样在发布分支完成之后代码修改最终会被合并回`develop`分支。如果`develop`分支急切需要这些修改，等不到发布分支完成，也可以同时安全地合并这些代码修改到`develop`分支。

最后，删除临时的热修复分支：

```
$ git branch -d hotfix-1.2.1
Deleted branch hotfix-1.2.1 (was abbe5d6).
```

# 总结

虽然与本文描述的分支模型相比没有太多新的内容，本文开始处的"大图"在我们的项目中非常有用。它形成了一种优美的心智模型，非常易于理解，并且让项目组成员之间对分支和发布流程有共同的理解。

[此处](http://nvie.com/files/Git-branching-model.pdf)提供有高质量的PDF版本，请将其打印出来并挂在公司的墙壁上以便时时参考。

# 翻译说明

本文为翻译文章，此为[原文链接](http://nvie.com/posts/a-successful-git-branching-model)。