/**
 * ==============================================
 * 文件名：Step02_State.jsx
 * 【基础功能】学习 useState — React 最核心的状态管理 Hook
 * 【核心学习知识点】
 *   1. useState — 让组件"记住"数据的 Hook
 *   2. 状态变化 → 自动重新渲染 — React 的核心工作机制
 *   3. 不可变更新 — 状态必须用 setXxx 修改，不能直接改
 *   4. 多个状态 — 一个组件可以有多个 useState
 *   5. 状态提升 — 兄弟组件共享状态的方法
 *   6. 对象/数组状态更新 — 展开运算符 [...] {...} 的正确用法
 * 【适用场景】React 开发 100% 必须掌握，每个组件都会用到
 * 【进阶说明】
 *   Hook 是 React 16.8 引入的新特性，让函数组件也能用状态（之前只有 Class 有状态）
 *   useState 内部用闭包+链表维护状态，每次渲染获取当前节点的状态值
 *   React 18 的自动批处理让多次 setState 只触发一次渲染
 * ==============================================
 */
import React, { useState } from 'react';

// ==============================================
// 子组件：计数器（演示最基本的 useState）
// 【基础】独立封装计数器逻辑，父组件可以复用多个计数器
// ==============================================
function Counter({ name }) {
  // 【基础】useState(0) — 创建状态变量
  //   count → 当前值（初始为 0）
  //   setCount → 修改 count 的函数（调用它 React 会自动重新渲染）
  const [count, setCount] = useState(0);

  return (
    <div className="learn-card" style={{ textAlign: 'center' }}>
      <h4>{name}</h4>
      <p style={{ fontSize: '2rem', fontWeight: 'bold', margin: '0.5rem 0' }}>{count}</p>
      {/* 【基础】onClick 点击事件，调用 setCount 修改状态 */}
      <button className="btn btn-primary" onClick={() => setCount(count + 1)}>
        +1
      </button>
      {' '}
      <button className="btn btn-primary" onClick={() => setCount(count - 1)}>
        -1
      </button>
      {' '}
      <button className="btn btn-danger" onClick={() => setCount(0)}>
        重置
      </button>
    </div>
  );
}

// ==============================================
// 子组件：Todo 清单（演示对象/数组状态）
// ==============================================
function TodoDemo() {
  // 【基础】数组状态 — 用 useState([]) 初始化为空数组
  const [todos, setTodos] = useState([
    { id: 1, text: '学习 React 组件', done: true },
    { id: 2, text: '学习 useState', done: false },
  ]);
  // 输入框的文本状态
  const [inputText, setInputText] = useState('');
  // 【进阶】nextId 用 useState 管理，确保每次自增都是唯一值
  //   用普通变量（let nextId = 3）在重新渲染时会重置
  const [nextId, setNextId] = useState(3);

  // ==============================================
  // 添加待办事项
  // 【基础】事件处理函数，被按钮 onClick 调用
  // 【进阶】不可变更新原则：必须用 setTodos 传入新数组
  //   ❌ 错误写法：todos.push(...) 然后 setTodos(todos) — 直接修改原数组
  //   ✅ 正确写法：setTodos([...todos, newTodo]) — 创建新数组
  //   原因：React 用 Object.is 比较新旧状态，直接修改不会触发渲染
  // ==============================================
  function handleAdd() {
    // 【基础】.trim() 去掉首尾空格，空内容不添加
    if (!inputText.trim()) return;
    // 【进阶】[...todos, newTodo] — 展开运算符，创建包含旧数据 + 新数据的新数组
    setTodos([...todos, { id: nextId, text: inputText, done: false }]);
    setNextId(nextId + 1); // 自增 ID
    setInputText(''); // 清空输入框
  }

  // 切换完成状态
  function handleToggle(id) {
    // 【基础】.map() 遍历数组，找到对应 id 的项，翻转 done 状态
    // 【进阶】{...todo, done: !todo.done} — 展开对象 + 覆盖特定属性
    //   也是不可变更新：创建新对象而不是修改原对象
    setTodos(todos.map((todo) =>
      todo.id === id ? { ...todo, done: !todo.done } : todo
    ));
  }

  // 删除待办
  function handleDelete(id) {
    // 【基础】.filter() 过滤数组，返回不包含被删除项的新数组
    setTodos(todos.filter((todo) => todo.id !== id));
  }

  return (
    <div>
      {/* 输入区域 */}
      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>
        <input
          className="input"
          type="text"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          placeholder="输入待办事项..."
          onKeyDown={(e) => e.key === 'Enter' && handleAdd()}
          style={{ marginBottom: 0 }}
        />
        <button className="btn btn-primary" onClick={handleAdd}>添加</button>
      </div>

      {/* 列表区域 */}
      {/* 【基础】条件渲染：列表为空时不显示 */}
      {todos.length === 0 ? (
        <p style={{ color: '#6b7280', textAlign: 'center' }}>暂无待办事项</p>
      ) : (
        <ul className="item-list">
          {todos.map((todo) => (
            <li key={todo.id}>
              <span
                onClick={() => handleToggle(todo.id)}
                style={{
                  cursor: 'pointer',
                  textDecoration: todo.done ? 'line-through' : 'none',
                  color: todo.done ? '#6b7280' : 'inherit',
                }}
              >
                {/* 【基础】根据 done 状态显示不同符号 */}
                {todo.done ? '✅' : '⬜'} {todo.text}
              </span>
              <button className="btn btn-danger" onClick={() => handleDelete(todo.id)}>
                删除
              </button>
            </li>
          ))}
        </ul>
      )}
      <p style={{ color: '#6b7280', fontSize: '0.85rem', marginTop: '0.5rem' }}>
        共 {todos.length} 项，
        已完成 {todos.filter((t) => t.done).length} 项
      </p>
    </div>
  );
}

export default function Step02_State() {
  return (
    <div>
      {/* ========== 1. 基础：计数器 ========== */}
      <div className="learn-card">
        <h3>
          <span className="tag tag-basic">基础</span> 1. useState 基础 — 计数器
        </h3>
        <p style={{ marginBottom: '0.75rem', color: '#6b7280' }}>
          点击按钮改变状态 → React 自动重新渲染 → 页面数字更新。
          这就是 React 的"声明式"哲学：你只管修改数据，React 负责更新 UI。
        </p>
        <div className="grid-2col">
          <Counter name="计数器 A" />
          <Counter name="计数器 B" />
        </div>
        <p style={{ fontSize: '0.85rem', color: '#6b7280', marginTop: '0.75rem' }}>
          两个计数器互相独立 — 每个组件有自己的状态，互不影响。
          这和"全局变量"不同，是 React 状态隔离的核心特性。
        </p>
      </div>

      {/* ========== 2. 进阶：Todo 清单 ========== */}
      <div className="learn-card">
        <h3>
          <span className="tag tag-advanced">进阶</span> 2. 对象/数组状态 — Todo 清单
        </h3>
        <p style={{ marginBottom: '0.75rem', color: '#6b7280' }}>
          演示数组的增删改操作 + 不可变更新原则。
          注意：每次修改都创建新数组/新对象，绝不直接修改原数据。
        </p>
        <TodoDemo />
      </div>

      {/* ========== 3. useState 原理拆解 ========== */}
      <div className="learn-card">
        <h3>
          <span className="tag tag-advanced">进阶</span> 3. useState 不可变更新的原理
        </h3>
        <div className="code-block">
{`// ===== React 状态更新的核心规则 =====

// ❌ 错误：直接修改数组（不会触发重新渲染！）
todos.push(newTodo);
setTodos(todos);

// ✅ 正确：创建新数组（React 检测到引用变化 → 重新渲染）
setTodos([...todos, newTodo]);

// ❌ 错误：直接修改对象属性
user.name = 'new name';
setUser(user);

// ✅ 正确：创建新对象
setUser({ ...user, name: 'new name' });

// ===== 原理 =====
// React 用 Object.is() 比较新旧状态（类似三等号 ===）
// 对象/数组是引用类型，直接修改只改变内容，引用不变
// Object.is(原数组, 修改后的数组) → true（同一个引用）
// React 认为"没变化"，跳过重新渲染
//
// 只有传入新对象/新数组，React 检测到引用变了 → 才重新渲染

// ===== 常见场景速查 =====
// 数组追加：setList([...list, item])
// 数组删除：setList(list.filter(i => i.id !== id))
// 数组修改：setList(list.map(i => i.id===id ? {...i, key:val} : i))
// 对象修改：setObj({ ...obj, key: newVal })`}
        </div>
      </div>
    </div>
  );
}
