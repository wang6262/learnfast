/**
 * ==============================================
 * 文件名：Step05_Effects.jsx
 * 【基础功能】学习 useEffect — React 的副作用处理 Hook
 * 【核心学习知识点】
 *   1. useEffect 概念 — "什么时候执行副作用"
 *   2. 依赖数组 [] — 控制何时重新执行
 *   3. 清理函数 — 组件卸载时的收尾工作
 *   4. 数据获取模式 — useEffect + fetch 获取后端数据
 *   5. 副作用种类 — DOM 操作、定时器、订阅、API 调用
 *   6. StrictMode 双次执行 — 开发环境调试行为
 * 【适用场景】
 *   API 数据获取、定时器 (setInterval)、事件监听、WebSocket 连接等
 *   任何"React 渲染之外"的操作都叫副作用，都在 useEffect 中处理
 * 【进阶说明】
 *   useEffect 是 Class 组件生命周期方法的替代：
 *   componentDidMount + componentDidUpdate + componentWillUnmount 三合一
 *   不同于生命周期的"时间点"思维，useEffect 是"同步状态"思维
 * ==============================================
 */
import React, { useState, useEffect } from 'react';

export default function Step05_Effects() {
  // ==============================================
  // 演示 1：基础 useEffect — 依赖变化时执行
  // ==============================================
  const [count, setCount] = useState(0);
  const [effectMessage, setEffectMessage] = useState('');

  // 【基础】useEffect(函数, 依赖数组)
  //   依赖数组 [count] → count 变化时执行函数
  useEffect(() => {
    setEffectMessage(`useEffect 触发！count 变成了 ${count}，时间：${new Date().toLocaleTimeString()}`);
    // 【进阶】没有返回清理函数 → 这个 effect 不需要清理
  }, [count]); // ← 依赖数组：只有 count 变化才执行
  // 【基础】[] 空依赖 → 只在组件首次渲染后执行一次（模拟 componentDidMount）

  // ==============================================
  // 演示 2：空依赖 [] — 仅在挂载时执行一次
  // 【基础】适合做"页面初始化"操作，比如首次获取数据
  // ==============================================
  const [mountedTime, setMountedTime] = useState('');

  useEffect(() => {
    // 组件挂载时记录时间（只执行一次）
    setMountedTime(new Date().toLocaleString());
  }, []); // 【关键】空数组 = 只在首次渲染后执行

  // ==============================================
  // 演示 3：定时器 + 清理函数
  // 【基础】清理函数在组件卸载时执行，防止内存泄漏
  //   如果没有清理，组件销毁后定时器仍然在跑！
  // ==============================================
  const [timer, setTimer] = useState(0);
  const [timerRunning, setTimerRunning] = useState(false);

  useEffect(() => {
    if (!timerRunning) return; // 未启动时不设置定时器

    // 【基础】setInterval 每隔 1 秒执行一次
    const id = setInterval(() => {
      setTimer((prev) => prev + 1); // 【进阶】用函数式更新，避免闭包陷阱
    }, 1000);

    // 【基础】清理函数：return 一个函数
    //   组件卸载或 timerRunning 变 false 时，先执行清理再重新执行 effect
    return () => {
      clearInterval(id); // 清除定时器，防止内存泄漏
    };
  }, [timerRunning]); // timerRunning 变化时重新执行

  // ==============================================
  // 演示 4：窗口尺寸监听 + 清理
  // ==============================================
  const [windowSize, setWindowSize] = useState({
    width: window.innerWidth,
    height: window.innerHeight,
  });

  useEffect(() => {
    function handleResize() {
      setWindowSize({ width: window.innerWidth, height: window.innerHeight });
    }

    // 【基础】绑定全局事件监听
    window.addEventListener('resize', handleResize);

    // 【进阶】清理函数：移除事件监听
    //   不清理的话，每次 effect 重新执行就多绑一个监听器，造成内存泄漏
    return () => {
      window.removeEventListener('resize', handleResize);
    };
  }, []); // 空依赖 = 只在挂载时绑定一次

  return (
    <div>
      {/* ========== 1. 基础 useEffect ========== */}
      <div className="learn-card">
        <h3>
          <span className="tag tag-basic">基础</span> 1. useEffect + 依赖数组
        </h3>
        <p style={{ marginBottom: '0.75rem', color: '#6b7280' }}>
          useEffect 在依赖数组中的值变化时执行。这是 React 处理"副作用"的标准方式。
        </p>
        <button className="btn btn-primary" onClick={() => setCount(count + 1)}>
          增加 count（当前：{count}）
        </button>
        <div className="result-box" style={{ marginTop: '0.5rem' }}>
          {effectMessage || '还没触发过...'}
        </div>

        <h4 style={{ marginTop: '1rem' }}>
          <span className="tag tag-advanced">进阶</span> 依赖数组的 3 种模式
        </h4>
        <div className="code-block">
{`// 模式 1：无依赖数组 → 每次渲染后都执行（几乎不用）
useEffect(() => {
  console.log('每次渲染都执行');
});

// 模式 2：空数组 [] → 只在首次渲染后执行一次
// 对应 Class 的 componentDidMount
useEffect(() => {
  fetchData(); // 页面初始化获取数据
}, []);

// 模式 3：指定依赖 [a, b] → a 或 b 变化时执行
// 对应 Class 的 componentDidUpdate
useEffect(() => {
  console.log('a 或 b 变了');
}, [a, b]);

// 清理函数：return 的函数在下一次执行前 或 组件卸载时调用
useEffect(() => {
  const subscription = subscribe();
  return () => subscription.unsubscribe(); // 清理
}, []);

// 组件生命周期映射：
// 挂载 → useEffect(..., []) 执行
// 更新 → useEffect(..., [dep]) 清理旧 → 执行新
// 卸载 → useEffect(..., [...]) 的清理函数执行`}
        </div>
      </div>

      {/* ========== 2. 清理函数 ========== */}
      <div className="learn-card">
        <h3>
          <span className="tag tag-advanced">进阶</span> 2. 清理函数 — 防止内存泄漏
        </h3>
        <p style={{ marginBottom: '0.75rem', color: '#6b7280' }}>
          清理函数 = useEffect 里 return 的函数。组件卸载时 React 会自动调用它做收尾工作。
        </p>

        {/* 定时器 */}
        <div style={{ marginBottom: '1rem' }}>
          <h4>计时器示例（带清理）：</h4>
          <p style={{ fontSize: '1.5rem', fontWeight: 'bold', margin: '0.5rem 0' }}>{timer} 秒</p>
          {!timerRunning ? (
            <button className="btn btn-primary" onClick={() => setTimerRunning(true)}>启动计时器</button>
          ) : (
            <button className="btn btn-danger" onClick={() => setTimerRunning(false)}>停止计时器</button>
          )}
          <button className="btn" style={{ marginLeft: '0.5rem', background: '#e5e7eb' }} onClick={() => setTimer(0)}>
            重置
          </button>
        </div>

        {/* 窗口尺寸 */}
        <div>
          <h4>窗口尺寸监听（带清理）：</h4>
          <p>
            当前窗口：<strong>{windowSize.width}</strong> × <strong>{windowSize.height}</strong>
          </p>
          <p style={{ fontSize: '0.85rem', color: '#6b7280' }}>试试缩放浏览器窗口 — 数值会实时更新</p>
        </div>

        <div className="code-block" style={{ marginTop: '0.75rem' }}>
{`// ===== 常见需要清理的场景 =====

// 1. 定时器
useEffect(() => {
  const id = setInterval(tick, 1000);
  return () => clearInterval(id); // ✅ 清理！
}, []);

// 2. 事件监听
useEffect(() => {
  window.addEventListener('resize', handler);
  return () => window.removeEventListener('resize', handler); // ✅ 清理！
}, []);

// 3. WebSocket
useEffect(() => {
  const ws = new WebSocket('ws://...');
  return () => ws.close(); // ✅ 清理！
}, []);

// 4. 数据订阅
useEffect(() => {
  const unsub = dataSource.subscribe(callback);
  return unsub; // ✅ 清理！
}, []);

// ⚠️ StrictMode 会让 effect 执行两次（仅开发环境）
// 挂载 → 卸载 → 再挂载，用来检测清理逻辑是否正确
// 如果你的 effect 在 StrictMode 下异常，说明缺少清理函数`}
        </div>
      </div>

      {/* ========== 3. 数据获取 ========== */}
      <div className="learn-card">
        <h3>
          <span className="tag tag-basic">基础</span> 3. 常见使用场景总结
        </h3>
        <div className="code-block">
{`// ===== 场景 1：页面初始化获取数据 =====
useEffect(() => {
  fetch('/api/users')
    .then(res => res.json())
    .then(data => setUsers(data));
}, []); // 空依赖，只执行一次

// ===== 场景 2：搜索（依赖变化时重新请求）=====
const [query, setQuery] = useState('');
useEffect(() => {
  if (query.length < 2) return;
  const timer = setTimeout(() => {
    fetch('/api/search?q=' + query)
      .then(res => res.json())
      .then(setResults);
  }, 300); // 防抖：300ms 内不再输入才发送请求
  return () => clearTimeout(timer); // 清理旧定时器
}, [query]); // query 变化触发

// ===== 场景 3：页面标题同步 =====
const [title, setTitle] = useState('首页');
useEffect(() => {
  document.title = title + ' | My App';
}, [title]);

// ===== 记住规律 =====
// 需要"React 之外"的事 → useEffect
// 依赖什么变量 → 放入依赖数组
// 需要取消订阅/清理 → return 清理函数`}
        </div>
      </div>

      {/* ========== 挂载时间 ========== */}
      <p style={{ color: '#6b7280', fontSize: '0.85rem', textAlign: 'center' }}>
        组件挂载时间：{mountedTime || '记录中...'}
      </p>
    </div>
  );
}
