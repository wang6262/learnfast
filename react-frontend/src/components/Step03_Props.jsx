/**
 * ==============================================
 * 文件名：Step03_Props.jsx
 * 【基础功能】学习 Props — React 组件之间的数据传递机制
 * 【核心学习知识点】
 *   1. Props 基本概念 — 父组件向子组件传数据（单向数据流）
 *   2. Props 解构 — 从参数中提取字段的简洁写法
 *   3. 默认值 — 未传参时的兜底值
 *   4. children — 特殊的 prop，传递 JSX 内容
 *   5. PropTypes vs TypeScript — 类型检查的两种方案
 *   6. Props 不可变原则 — 子组件只能读取，不能修改 Props
 * 【适用场景】所有组件通信都依赖 Props
 * 【进阶说明】
 *   单向数据流是 React 的核心设计：数据总是从父组件流向子组件
 *   这种设计让数据流动可预测，方便调试（不需要追踪"谁改了数据"）
 *   Props 传到子组件后，子组件用 state 或事件通知父组件来间接"修改"
 * ==============================================
 */
import React from 'react';

// ==============================================
// 子组件 1：基础 Props 演示
// 【基础】函数参数就是 Props，用 {} 解构提取需要的字段
// ==============================================
function Greeting({ name, age, city = '未知' }) {
  // city 有默认值：父组件没传 city 时显示"未知"
  return (
    <p>
      <strong>{name}</strong>，{age} 岁，来自 {city}
    </p>
  );
}

// ==============================================
// 子组件 2：children 演示
// 【基础】children 是 Props 中的特殊属性
//   <Card>这里面就是 children</Card> — 组件标签之间的内容
// 【进阶】children 让组件成为"容器"，类似 HTML 中的 div
//   这是一个强大的组合模式：组件不关心内容是什么，只负责"包裹"它
// ==============================================
function Card({ title, children, footer }) {
  return (
    <div className="learn-card">
      {title && (
        <h3 style={{ borderBottom: '1px solid #e5e7eb', paddingBottom: '0.5rem', marginBottom: '0.75rem' }}>
          {title}
        </h3>
      )}
      {/* 【基础】{children} 渲染组件标签之间的内容 */}
      <div>{children}</div>
      {/* 【进阶】footer 也是类似 children 的 slot（插槽）模式 */}
      {footer && (
        <div style={{ borderTop: '1px solid #e5e7eb', marginTop: '0.75rem', paddingTop: '0.5rem', fontSize: '0.85rem', color: '#6b7280' }}>
          {footer}
        </div>
      )}
    </div>
  );
}

// ==============================================
// 子组件 3：Props 透传（展开运算符）
// 【进阶】把父组件传入的所有 Props 透传给子组件
//   类似 Python 的 **kwargs 解包，非常实用的模式
// ==============================================
function StyledButton({ variant = 'primary', children, ...rest }) {
  // 【进阶】...rest 收集所有额外的 Props（onClick、disabled 等）
  //   然后 ...rest 展开传给原生 button 元素，实现"透传"
  const variantClass = variant === 'danger' ? 'btn-danger' : 'btn-primary';
  return (
    <button className={`btn ${variantClass}`} {...rest}>
      {children}
    </button>
  );
}

// ==============================================
// 子组件 4：通知父组件（反向通信）
// 【基础】"修改 Props"的正确方式：子组件调用父组件传来的函数
//   这就是"状态提升"模式：状态存在父组件，子组件通过回调函数通知修改
// ==============================================
function LikeButton({ liked, onToggle }) {
  return (
    <button
      className={`btn ${liked ? 'btn-danger' : 'btn-primary'}`}
      onClick={onToggle}
    >
      {liked ? '❤️ 已点赞' : '🤍 点赞'}
    </button>
  );
}

export default function Step03_Props() {
  // 点赞状态 — 存在父组件中（状态提升）
  const [liked, setLiked] = React.useState(false);
  // 点击计数 — 演示状态提升
  const [clickCount, setClickCount] = React.useState(0);

  function handleToggle() {
    setLiked(!liked);
    setClickCount(clickCount + 1);
  }

  return (
    <div>
      {/* ========== 1. Props 基础 ========== */}
      <div className="learn-card">
        <h3>
          <span className="tag tag-basic">基础</span> 1. Props 基础 — 父传子数据
        </h3>
        <p style={{ marginBottom: '0.75rem', color: '#6b7280' }}>
          Props（Properties 的缩写）是父组件传给子组件的数据，类似于函数调用时的参数。
          数据从上向下流（单向数据流），这是 React 的核心设计原则。
        </p>
        {/* 【基础】向子组件传入 Props：属性名=值 */}
        <Greeting name="张三" age={25} city="北京" />
        <Greeting name="李四" age={30} city="上海" />
        {/* city 没传，使用默认值"未知" */}
        <Greeting name="王五" age={28} />

        <h4 style={{ marginTop: '1rem' }}>
          <span className="tag tag-advanced">进阶</span> Props 是只读的
        </h4>
        <div className="code-block">
{`// 子组件中绝对不能这样做（React 会报错/不生效）：
function Child({ name }) {
  name = "new name";   // ❌ 修改 Props
  return <p>{name}</p>;
}

// Props 只读是 React 的硬性规则（单向数据流）
// 它是为了让你可以追踪数据的来源和变化
// 如果子组件能改 Props，数据流就会混乱不可预测

// 需要通过"通知父组件"的方式来改变数据（见第 4 节）`}
        </div>
      </div>

      {/* ========== 2. children 模式 ========== */}
      <div className="learn-card">
        <h3>
          <span className="tag tag-advanced">进阶</span> 2. children — 组件变成"容器"
        </h3>
        <p style={{ marginBottom: '0.75rem', color: '#6b7280' }}>
          children 是最常用的组合模式。可以理解成"把一段 JSX 传给组件，组件决定怎么包裹和展示它"。
        </p>
        <Card title="用户信息" footer="最后更新：2026-07-07">
          {/* 【基础】标签之间的内容就是 children */}
          <Greeting name="赵六" age={35} city="深圳" />
          <p style={{ color: '#6b7280', marginTop: '0.5rem' }}>
            这些内容通过 children 传入 Card 组件
          </p>
        </Card>

        <div className="code-block">
{`// Card 组件内部：
function Card({ title, children, footer }) {
  return (
    <div className="card">
      {title && <h3>{title}</h3>}
      {children}    ← 这里渲染 <Card>...</Card> 之间的内容
      {footer && <div>{footer}</div>}
    </div>
  );
}

// 使用：
<Card title="标题" footer="脚注">
  <p>这是插入的内容</p>  ← 这整个就是 children
</Card>

// 对比：
// 普通 Props：<User name="张三" /> — 数据是 JS 值
// children：<Card><p>内容</p></Card> — 数据是完整的 UI 片段`}
        </div>
      </div>

      {/* ========== 3. Props 透传 ========== */}
      <div className="learn-card">
        <h3>
          <span className="tag tag-advanced">进阶</span> 3. Props 透传 — 展开运算符 ...rest
        </h3>
        <p style={{ marginBottom: '0.75rem', color: '#6b7280' }}>
          当你想封装一个原生元素（如 button、input），但保留所有原生属性时使用。
        </p>
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
          <StyledButton variant="primary" onClick={() => alert('被点击了！')}>
            普通按钮
          </StyledButton>
          <StyledButton variant="danger" onClick={() => alert('危险操作！')}>
            危险按钮
          </StyledButton>
        </div>
        <div className="code-block" style={{ marginTop: '0.75rem' }}>
{`// ...rest 收集剩余 Props，然后透传给原生 button
function StyledButton({ variant, children, ...rest }) {
  return <button className={variant} {...rest}>{children}</button>;
}

// 使用时，onClick 通过 ...rest 传到底层 button
<StyledButton onClick={handleClick}>点击</StyledButton>

// 类似 Python 的 **kwargs：
// def styled_button(**kwargs):
//     return Button(**kwargs)`}
        </div>
      </div>

      {/* ========== 4. 通知父组件 ========== */}
      <div className="learn-card">
        <h3>
          <span className="tag tag-advanced">进阶</span> 4. 子组件通知父组件 — 状态提升
        </h3>
        <p style={{ marginBottom: '0.75rem', color: '#6b7280' }}>
          Props 不能修改 → 状态存在父组件 → 子组件通过"回调函数"通知父组件修改。
          这就是状态提升（Lifting State Up）。
        </p>
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
          <LikeButton liked={liked} onToggle={handleToggle} />
          <span style={{ color: '#6b7280' }}>累计点击：{clickCount} 次</span>
        </div>
        <div className="code-block" style={{ marginTop: '0.75rem' }}>
{`// ===== 状态提升模式 =====

// 1. 状态存在父组件（离需要的组件最近的公共祖先）
function Parent() {
  const [liked, setLiked] = useState(false);
  return <Child liked={liked} onToggle={() => setLiked(!liked)} />;
}

// 2. 子组件通过回调函数通知父组件
function Child({ liked, onToggle }) {
  return <button onClick={onToggle}>{liked ? '❤️' : '🤍'}</button>;
}

// 数据流：Parent --liked--> Child（正常 Props 向下）
// 通知流：Child --onToggle--> Parent（回调函数向上）
// 实际修改在 Parent 中：setLiked → 自动重新渲染 → 新 liked 传给 Child

// 这就是 React 的数据管理基础模式
// 当应用变大后，这种模式会变繁琐 → 引出 Context / Redux / Zustand`}
        </div>
      </div>
    </div>
  );
}
