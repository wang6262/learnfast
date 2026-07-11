/**
 * ==============================================
 * 文件名：Step04_Events.jsx
 * 【基础功能】学习 React 事件处理 + 表单受控组件
 * 【核心学习知识点】
 *   1. React 事件系统 — onClick/onChange/onSubmit 等
 *   2. 合成事件 — React 对原生事件的封装（跨浏览器兼容）
 *   3. 受控组件 — 表单的值由 React state 控制
 *   4. 非受控组件 — 用 ref 直接读 DOM（少数场景）
 *   5. 表单提交 — onSubmit + preventDefault
 *   6. 事件处理中的 this 问题（Class 组件才有，函数组件直接用函数）
 * 【适用场景】任何需要交互的 React 应用都离不开事件处理
 * 【进阶说明】
 *   React 事件（合成事件）和原生事件不同：
 *   1. 事件名用驼峰：onClick 而非 onclick
 *   2. 传函数而非字符串："handleClick" 是错的，{handleClick} 才对
 *   3. e.preventDefault() 必须显式调用（不像 HTML 中 return false）
 *   4. React 17+ 事件委托在 root 节点，17 以下在 document
 * ==============================================
 */
import React, { useState, useRef } from 'react';

export default function Step04_Events() {
  // ==============================================
  // 演示 1：点击事件 + 事件对象
  // ==============================================
  const [clickInfo, setClickInfo] = useState('未点击');

  function handleClick(e) {
    // e 是 React 的合成事件对象（SyntheticEvent）
    // 兼容所有主流浏览器，不用处理 IE 的事件差异
    setClickInfo(`点击了！坐标 (${e.clientX}, ${e.clientY})，目标: ${e.target.tagName}`);
  }

  // ==============================================
  // 演示 2：受控表单
  // 【基础】受控组件 = 表单 value 由 state 控制
  //   输入框的值 = state 变量，onChange 时更新 state → 值同步
  //   React 是表单数据的"唯一真理来源"
  // ==============================================
  const [form, setForm] = useState({
    username: '',
    email: '',
    bio: '',
    role: 'viewer', // 下拉框
  });
  const [submitted, setSubmitted] = useState(null);

  // 【进阶】通用 onChange 处理 — 用 name 属性区分字段
  //   一个函数处理所有字段的输入，根据 e.target.name 更新对应 state
  //   对比：每个字段写一个 handler 太冗余
  function handleChange(e) {
    const { name, value } = e.target; // 解构获取字段名和当前输入值
    // 【进阶】...form 展开旧对象，[name]: value 动态更新对应字段
    setForm({ ...form, [name]: value });
  }

  function handleSubmit(e) {
    e.preventDefault(); // 【基础】阻止表单默认提交（页面会刷新，SPA 不需要）
    setSubmitted({ ...form, time: new Date().toLocaleString() });
  }

  // ==============================================
  // 演示 3：非受控组件（useRef）
  // 【进阶】ref 直接访问真实 DOM，少数场景使用（文件上传、焦点管理、第三方库集成）
  // ==============================================
  const fileInputRef = useRef(null);
  const [fileName, setFileName] = useState('未选择文件');

  function handleFileSelect() {
    // 【进阶】通过 ref.current 访问真实 DOM，直接读取文件信息
    //   这一步不经过 React state，性能更高（大文件场景）
    const file = fileInputRef.current?.files?.[0];
    setFileName(file ? `${file.name} (${(file.size / 1024).toFixed(1)} KB)` : '未选择文件');
  }

  // ==============================================
  // 演示 4：键盘事件
  // ==============================================
  const [lastKey, setLastKey] = useState('无');
  const [keyLog, setKeyLog] = useState([]);

  function handleKeyDown(e) {
    setLastKey(`${e.key} (code: ${e.code})`);
    // 仅记录非重复按键（按住不放时 key 事件会重复触发）
    if (!e.repeat) {
      setKeyLog((prev) => {
        const newLog = [...prev, e.key];
        return newLog.length > 20 ? newLog.slice(-20) : newLog;
      });
    }
  }

  return (
    <div>
      {/* ========== 1. 点击事件 ========== */}
      <div className="learn-card">
        <h3>
          <span className="tag tag-basic">基础</span> 1. 点击事件 — onClick
        </h3>
        <p style={{ marginBottom: '0.75rem', color: '#6b7280' }}>
          onClick 是最常用的事件。React 事件名用驼峰命名（onClick 而非 onclick）。
        </p>
        <button className="btn btn-primary" onClick={handleClick}>
          点击获取事件信息
        </button>
        <p style={{ marginTop: '0.5rem', fontSize: '0.9rem' }}>{clickInfo}</p>

        <h4 style={{ marginTop: '1rem' }}>
          <span className="tag tag-advanced">进阶</span> 合成事件 vs 原生事件
        </h4>
        <div className="code-block">
{`// React 合成事件（SyntheticEvent）关键点：

// 1. 事件名驼峰：HTML 的 onclick → React 的 onClick
// 2. 传函数引用（不是调用结果）：
//    ✅ onClick={handleClick}     — 正确，传函数本身
//    ❌ onClick={handleClick()}   — 错误，传的是函数的返回值
// 3. 需要传参时用箭头函数：
//    onClick={() => handleClick(id)}  — 这会创建一个新函数
// 4. preventDefault 必须显式调用：
//    HTML:  <form onsubmit="return false">
//    React: <form onSubmit={e => e.preventDefault()}>

// React 17+ 事件不再委托到 document，而是 root 节点
// 好处：多个 React 版本共存不会互相干扰（微前端场景）`}
        </div>
      </div>

      {/* ========== 2. 受控表单 ========== */}
      <div className="learn-card">
        <h3>
          <span className="tag tag-basic">基础</span> 2. 受控组件 — 表单数据由 state 管理
        </h3>
        <p style={{ marginBottom: '0.75rem', color: '#6b7280' }}>
          受控组件 = 表单的 value 绑定 state + onChange 更新 state。
          State 是表单数据的"唯一真理来源"。
        </p>
        <form onSubmit={handleSubmit}>
          <div className="grid-2col">
            <div className="form-group">
              <label>用户名：</label>
              <input
                className="input"
                name="username"
                value={form.username}
                onChange={handleChange}
                placeholder="请输入用户名"
                required
              />
            </div>
            <div className="form-group">
              <label>邮箱：</label>
              <input
                className="input"
                name="email"
                type="email"
                value={form.email}
                onChange={handleChange}
                placeholder="请输入邮箱"
              />
            </div>
          </div>
          <div className="form-group">
            <label>个人简介：</label>
            <textarea
              className="input"
              name="bio"
              value={form.bio}
              onChange={handleChange}
              rows={3}
              placeholder="介绍一下自己..."
            />
          </div>
          <div className="form-group">
            <label>角色：</label>
            <select className="input" name="role" value={form.role} onChange={handleChange}>
              <option value="admin">管理员</option>
              <option value="editor">编辑者</option>
              <option value="viewer">观察者</option>
            </select>
          </div>
          <button className="btn btn-primary" type="submit">提交表单</button>
          <button
            className="btn"
            type="button"
            style={{ marginLeft: '0.5rem', background: '#e5e7eb' }}
            onClick={() => setForm({ username: '', email: '', bio: '', role: 'viewer' })}
          >
            重置
          </button>
        </form>

        {/* 实时预览（受控组件的优势！） */}
        <h4 style={{ marginTop: '1rem' }}>
          <span className="tag tag-advanced">进阶</span> 实时输入预览
        </h4>
        <div className="result-box">
{`{
  username: "${form.username}",
  email: "${form.email}",
  bio: "${form.bio}",
  role: "${form.role}"
}`}
        </div>

        {/* 提交结果显示 */}
        {submitted && (
          <div className="result-box" style={{ marginTop: '0.5rem' }}>
            {`提交成功！（${submitted.time}）\n${JSON.stringify(submitted, null, 2)}`}
          </div>
        )}
      </div>

      {/* ========== 3. 非受控组件 ========== */}
      <div className="learn-card">
        <h3>
          <span className="tag tag-advanced">进阶</span> 3. 非受控组件 — useRef 直接读 DOM
        </h3>
        <p style={{ marginBottom: '0.75rem', color: '#6b7280' }}>
          大多数场景用受控组件。非受控组件适合：文件上传、手动焦点管理、集成非 React 库。
        </p>
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
          <button className="btn btn-primary" onClick={() => fileInputRef.current?.click()}>
            选择文件
          </button>
          {/* 【基础】ref 绑定到 DOM 元素 */}
          <input
            ref={fileInputRef}
            type="file"
            style={{ display: 'none' }}
            onChange={handleFileSelect}
          />
          <span style={{ color: '#6b7280' }}>{fileName}</span>
        </div>
      </div>

      {/* ========== 4. 键盘事件 ========== */}
      <div className="learn-card">
        <h3>
          <span className="tag tag-basic">基础</span> 4. 键盘事件 — onKeyDown
        </h3>
        <p style={{ marginBottom: '0.75rem', color: '#6b7280' }}>
          在这里按下键盘试试（onKeyDown 绑定在整个卡片上）。
        </p>
        {/* tabIndex 让非交互元素也可以接收键盘事件 */}
        {/* 【进阶】onKeyDown 必须配合 tabIndex 才能让 div 获得键盘焦点 */}
        <div
          className="result-box"
          tabIndex={0}
          onKeyDown={handleKeyDown}
          style={{ outline: 'none', cursor: 'text' }}
        >
          <p>最后按下的键：{lastKey}</p>
          <p style={{ color: '#6b7280', marginTop: '0.5rem' }}>
            按键记录（最近 20 次）：{keyLog.join(' + ') || '无'}
          </p>
        </div>
      </div>
    </div>
  );
}
