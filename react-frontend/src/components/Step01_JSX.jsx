/**
 * ==============================================
 * 文件名：Step01_JSX.jsx
 * 【基础功能】学习 React 最核心的概念 — JSX（在 JS 里写 HTML）
 * 【核心学习知识点】
 *   1. JSX 语法规则 — 像写 HTML 一样写 UI
 *   2. 组件 — 把 UI 拆成可复用的积木块
 *   3. {} 表达式 — 在 HTML 中嵌入 JS 变量/逻辑
 *   4. 列表渲染 — 用 .map() 批量生成 HTML
 *   5. 条件渲染 — 根据条件显示/隐藏内容
 *   6. 组件嵌套 — 大组件包含小组件（搭积木思想）
 * 【适用场景】React 入门第一课，理解"组件化"思想
 * 【运行方式】npm run dev → 导航栏点击 Step 1
 * 【进阶说明】
 *   JSX 不是 HTML，是 JS 的语法糖，构建时会被 Babel 编译成 React.createElement()
 *   所以 JSX 中可以写任意 JS 表达式（在 {} 内），但不能写 JS 语句（if/for 不行）
 * ==============================================
 */
import React from 'react';

// ==============================================
// 子组件演示：用户信息卡片
// 【基础】组件就是函数，返回 JSX，首字母必须大写
// 【进阶】组件名大写是 React 的硬性规定 — JSX 中以大写开头判定为组件，小写判定为 HTML 标签
// ==============================================
function UserCard({ name, role }) {
  // 【基础】在 JSX 中用 {} 可以嵌入 JS 变量
  return (
    <div className="learn-card" style={{ textAlign: 'center' }}>
      <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>👤</div>
      <h3>{name}</h3>
      {/* 【基础】style 接收一个 JS 对象，驼峰命名 */}
      <p style={{ color: '#6b7280' }}>{role}</p>
    </div>
  );
}

export default function Step01_JSX() {
  // ==============================================
  // 数据：独立于 UI，方便修改
  // 【基础】数据定义在组件内，和显示逻辑分离
  //   这种"数据驱动视图"是 React 的核心理念
  //   数据变了 → UI 自动变（不需要手动更新 DOM）
  // ==============================================
  const title = '欢迎学习 React';
  const description = 'React 让你用声明式的方式构建 UI，你只管描述"UI 应该长什么样"，React 负责把它渲染出来。';

  // 用户列表数据（模拟从后端获取）
  const users = [
    { id: 1, name: '张三', role: '前端工程师' },
    { id: 2, name: '李四', role: '全栈开发者' },
    { id: 3, name: '王五', role: '后端工程师' },
  ];

  // 当前登录状态（用于条件渲染演示）
  const isLoggedIn = true;

  return (
    <div>
      {/* ========== 1. JSX 表达式 ========== */}
      <div className="learn-card">
        <h3>
          <span className="tag tag-basic">基础</span> 1. JSX 表达式 — 用 {} 在 HTML 中嵌入 JS
        </h3>
        {/* 【基础】{} 里可以放：变量、表达式、函数调用、三元运算 */}
        {/*   {} 里不能放：if 语句、for 循环、代码块（这些是 JS 语句不是表达式） */}
        <p><strong>标题：</strong>{title}</p>
        <p><strong>描述：</strong>{description}</p>
        <p><strong>当前时间：</strong>{new Date().toLocaleString()}</p>
        {/* 【基础】模板字符串 + 表达式混合 */}
        <p><strong>用户数量：</strong>{users.length} 人</p>

        <h4 style={{ marginTop: '1rem' }}>
          <span className="tag tag-advanced">进阶</span> JSX 编译原理
        </h4>
        <div className="code-block">
{`// JSX 写的是这样：
const element = <h1 className="title">Hello {name}</h1>;

// Babel 编译后实际是这样：
const element = React.createElement(
  "h1",
  { className: "title" },
  "Hello ",
  name
);

// 所以 JSX 就是 React.createElement 的语法糖
// 理解了这一点，就能明白为什么：
// 1. 组件必须大写（否则被当成字符串标签名）
// 2. className 用驼峰（createElement 接收的是 JS 对象属性）
// 3. JSX 中 {} 里写的是 JS 表达式，最终作为函数参数传入`}
        </div>
      </div>

      {/* ========== 2. 列表渲染 ========== */}
      <div className="learn-card">
        <h3>
          <span className="tag tag-basic">基础</span> 2. 列表渲染 — 用 .map() 批量生成 JSX
        </h3>
        <p style={{ marginBottom: '0.75rem', color: '#6b7280' }}>
          数据中每个用户 → JSX 中生成一个卡片，自动渲染。数据和 UI 一一对应。
        </p>
        {/* 【基础】.map() 遍历数组，把每个元素转成 JSX */}
        {/*   key 属性必须有（帮助 React 高效更新列表，通常用唯一 ID） */}
        <div className="grid-2col">
          {users.map((user) => (
            <UserCard key={user.id} name={user.name} role={user.role} />
          ))}
        </div>

        <h4 style={{ marginTop: '1rem' }}>
          <span className="tag tag-advanced">进阶</span> key 的作用
        </h4>
        <p style={{ fontSize: '0.85rem', color: '#6b7280' }}>
          React 用 key 追踪列表中的每个元素。列表更新时，React 通过 key 知道哪些元素变了，
          只重新渲染变化的部分（Diff 算法 + 虚拟 DOM）。key 必须唯一且稳定，通常用数据库 ID。
          绝对不能用数组索引作为 key — 列表顺序改变时会导致渲染错乱。
        </p>
      </div>

      {/* ========== 3. 条件渲染 ========== */}
      <div className="learn-card">
        <h3>
          <span className="tag tag-basic">基础</span> 3. 条件渲染 — 根据不同条件显示不同 UI
        </h3>
        {/* 【基础】三元表达式是最常用的条件渲染方式 */}
        {/*   条件 ? 显示这个 : 显示那个 */}
        <p>
          登录状态：{isLoggedIn ? (
            <span style={{ color: '#059669', fontWeight: 'bold' }}>已登录</span>
          ) : (
            <span style={{ color: '#dc2626', fontWeight: 'bold' }}>未登录</span>
          )}
        </p>
        {/* 【基础】&& 短路运算符 — 只有 isLoggedIn 为 true 时才显示后面的内容 */}
        {isLoggedIn && (
          <p style={{ color: '#6b7280', marginTop: '0.5rem' }}>
            这条消息只在登录后显示。（使用 && 运算符的条件渲染）
          </p>
        )}

        <h4 style={{ marginTop: '1rem' }}>
          <span className="tag tag-advanced">进阶</span> 条件渲染的 3 种写法对比
        </h4>
        <div className="code-block">
{`// 方式 1：三元表达式（最常用，适合二选一的情况）
{isLoggedIn ? <Dashboard /> : <Login />}

// 方式 2：&& 短路（适合"有就显示没有就不显示"）
{unreadCount > 0 && <Badge count={unreadCount} />}

// 方式 3：独立变量 + if（适合复杂条件逻辑）
let content;
if (loading) content = <Spinner />;
else if (error) content = <Error />;
else content = <Data />;
{content}

// 注意：&& 左边的值如果是 0/false，会渲染出 0 到页面上
// 如 {count && <p>{count}</p>}（count=0 时页面出现个 0）
// 安全写法：{count > 0 && <p>{count}</p>}`}
        </div>
      </div>

      {/* ========== 4. 组件嵌套 ========== */}
      <div className="learn-card">
        <h3>
          <span className="tag tag-advanced">进阶</span> 4. 组件嵌套 — 像搭积木一样构建页面
        </h3>
        <p style={{ color: '#6b7280', marginBottom: '0.75rem' }}>
          每个组件只做一件事，然后组合起来。这就是 React 的"组合"思想。
        </p>
        <div className="code-block">
{`// 典型页面结构（组件树）
<App>                           ← 根组件
  <Header />                    ← 导航栏组件
  <MainContent>                 ← 主内容区组件
    <Sidebar />                 ← 侧边栏组件
    <ArticleList>               ← 文章列表组件
      <ArticleCard />           ← 文章卡片组件
      <ArticleCard />           ← 复用同一个组件
    </ArticleList>
  </MainContent>
  <Footer />                    ← 底部组件
</App>

// 组件嵌套的核心原则（React 官方推荐）：
// 1. 单一职责：每个组件只做一件事
// 2. 组合优于继承：用嵌套代替继承（React 几乎不需要继承）
// 3. 数据从上往下流：Props 从父组件传给子组件`}
        </div>
      </div>
    </div>
  );
}
