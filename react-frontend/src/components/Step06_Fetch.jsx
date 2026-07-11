/**
 * ==============================================
 * 文件名：Step06_Fetch.jsx
 * 【基础功能】学习 React 如何调用 FastAPI 后端接口
 * 【核心学习知识点】
 *   1. fetch 请求生命周期 — loading → success → error 三态管理
 *   2. 跨域问题 — CORS 的本质和 Vite proxy 解决方案
 *   3. async/await 错误处理 — try/catch 包裹异步请求
 *   4. 请求状态管理 — 用 state 管理 loading/error/data
 *   5. 自定义 Hook — 封装可复用的请求逻辑（useRequest）
 * 【适用场景】任何需要前后端通信的 Web 应用
 * 【前置条件】需要 FastAPI 后端在 http://localhost:8000 运行
 *   启动方法：在项目根目录执行 uv run python step01_hello_fastapi.py
 * 【进阶说明】
 *   实际项目中数据获取有多种方案：
 *   1. React Query (TanStack Query) — 生产级方案，自动缓存/重取/去重
 *   2. SWR — 类似 React Query，Vercel 出品
 *   3. RTK Query — Redux Toolkit 内置方案
 *   4. 手写 useEffect + fetch — 学习阶段先掌握这个，理解原理
 * ==============================================
 */
import React, { useState, useEffect, useCallback } from 'react';

// 【进阶】动态获取 API 地址
//   因为 Vite proxy 只有在 dev server 运行时才生效
//   如果直接打开 index.html 文件（没有 dev server），需要完整 URL
const API_BASE = '/api';

// ==============================================
// 自定义 Hook：封装通用的请求逻辑
// 【进阶】把请求状态管理抽成一个 Hook，任何组件都能复用
//   这就是"关注点分离"：组件只管渲染，Hook 管数据获取
//   类似后端的 Repository 模式 — 一层抽象封装数据访问细节
// ==============================================
function useRequest() {
  const [data, setData] = useState(null);      // 响应数据
  const [loading, setLoading] = useState(false); // 加载中？
  const [error, setError] = useState(null);     // 错误信息
  const [statusCode, setStatusCode] = useState(null); // HTTP 状态码

  // 【基础】执行请求的核心函数
  //   useCallback 缓存函数引用，避免子组件不必要的重新渲染
  //   依赖数组为空 → 函数引用永远不变（类似模块级函数）
  const run = useCallback(async (path, options = {}) => {
    setLoading(true);
    setError(null);
    setData(null);

    try {
      // 【基础】fetch 请求
      //   await 等待 Promise → response 拿到响应对象
      const response = await fetch(API_BASE + path, {
        headers: { 'Content-Type': 'application/json', ...options.headers },
        ...options,
      });
      setStatusCode(response.status);

      // 【基础】判断 HTTP 状态码
      if (!response.ok) {
        const errBody = await response.json().catch(() => ({}));
        throw new Error(errBody.detail || `HTTP ${response.status}`);
      }

      // 解析 JSON
      const json = response.status === 204 ? null : await response.json();
      setData(json);
    } catch (err) {
      // 【基础】网络错误（后端没启动、断网等）会走到这里
      //   fetch 不把 HTTP 错误当异常，只把网络故障当异常
      setError(err.message);
    } finally {
      // 【基础】finally 不管成功失败都会执行，确保 loading 一定关闭
      setLoading(false);
    }
  }, []); // 空依赖：函数引用不变

  return { data, loading, error, statusCode, run };
}

export default function Step06_Fetch() {
  // 【基础】使用自定义 Hook 管理请求状态
  const { data, loading, error, statusCode, run } = useRequest();
  const [endpoint, setEndpoint] = useState('/users/');
  const [method, setMethod] = useState('GET');
  const [requestBody, setRequestBody] = useState('');
  const [responseTime, setResponseTime] = useState(null);

  // ==============================================
  // 发起请求
  // ==============================================
  async function handleSendRequest() {
    const startTime = Date.now();

    const options = { method };
    // POST/PUT/PATCH 时，如果填了 body，附带 JSON 请求体
    if (['POST', 'PUT', 'PATCH'].includes(method) && requestBody.trim()) {
      try {
        options.body = JSON.stringify(JSON.parse(requestBody));
      } catch {
        alert('请求体不是合法的 JSON 格式！');
        return;
      }
    }

    await run(endpoint, options);
    setResponseTime(Date.now() - startTime);
  }

  // ==============================================
  // 预设示例
  // ==============================================
  const examples = [
    { label: 'GET /users/', endpoint: '/users/', method: 'GET', body: '' },
    { label: 'GET /users/1', endpoint: '/users/1', method: 'GET', body: '' },
    { label: 'POST 创建用户', endpoint: '/users/', method: 'POST', body: '{"username":"test","email":"t@t.com"}' },
    { label: 'GET /docs', endpoint: '/docs', method: 'GET', body: '' },
    { label: 'GET /info', endpoint: '/info', method: 'GET', body: '' },
  ];

  return (
    <div>
      {/* ========== 1. 请求构造器 ========== */}
      <div className="learn-card">
        <h3>
          <span className="tag tag-basic">基础</span> 1. HTTP 请求构造器 — 连接到 FastAPI 后端
        </h3>
        <p style={{ marginBottom: '0.75rem', color: '#6b7280' }}>
          选择请求方法和端点，点击发送即可看到后端返回的数据。
          Vite proxy 会将 /api/* 请求转发到 localhost:8000。
        </p>

        {/* 预设示例 */}
        <div style={{ marginBottom: '0.75rem' }}>
          <strong style={{ fontSize: '0.85rem' }}>快速示例：</strong>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem', marginTop: '0.25rem' }}>
            {examples.map((ex, i) => (
              <button
                key={i}
                className="btn"
                style={{ fontSize: '0.75rem', background: '#e5e7eb', padding: '0.3rem 0.55rem' }}
                onClick={() => {
                  setEndpoint(ex.endpoint);
                  setMethod(ex.method);
                  setRequestBody(ex.body);
                }}
              >
                {ex.label}
              </button>
            ))}
          </div>
        </div>

        {/* 请求配置 */}
        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'flex-end', flexWrap: 'wrap' }}>
          <div style={{ width: '80px' }}>
            <label style={{ fontSize: '0.8rem', fontWeight: 600 }}>方法：</label>
            <select className="input" value={method} onChange={(e) => setMethod(e.target.value)}>
              {['GET', 'POST', 'PUT', 'PATCH', 'DELETE'].map((m) => (
                <option key={m} value={m}>{m}</option>
              ))}
            </select>
          </div>
          <div style={{ flex: 1, minWidth: '200px' }}>
            <label style={{ fontSize: '0.8rem', fontWeight: 600 }}>端点：</label>
            <input
              className="input"
              value={endpoint}
              onChange={(e) => setEndpoint(e.target.value)}
              placeholder="/users/"
            />
          </div>
          <button className="btn btn-primary" onClick={handleSendRequest} disabled={loading}>
            {loading ? '请求中...' : '发送请求'}
          </button>
        </div>

        {/* POST Body */}
        {['POST', 'PUT', 'PATCH'].includes(method) && (
          <div style={{ marginTop: '0.75rem' }}>
            <label style={{ fontSize: '0.8rem', fontWeight: 600 }}>请求体 (JSON)：</label>
            <textarea
              className="input"
              value={requestBody}
              onChange={(e) => setRequestBody(e.target.value)}
              rows={3}
              placeholder='{"username":"hello","email":"h@e.com"}'
              style={{ fontFamily: 'monospace', fontSize: '0.8rem' }}
            />
          </div>
        )}
      </div>

      {/* ========== 2. 响应展示 ========== */}
      <div className="learn-card">
        <h3>
          <span className="tag tag-basic">基础</span> 2. 响应结果
        </h3>

        {/* 状态指示器 */}
        <div style={{ display: 'flex', gap: '1rem', marginBottom: '0.75rem', fontSize: '0.9rem' }}>
          <span>
            状态：
            {loading ? (
              <span style={{ color: '#2563eb' }}>⏳ 加载中...</span>
            ) : statusCode ? (
              <span style={{ color: statusCode < 400 ? '#059669' : '#dc2626', fontWeight: 'bold' }}>
                HTTP {statusCode}
              </span>
            ) : (
              <span style={{ color: '#6b7280' }}>等待请求</span>
            )}
          </span>
          {responseTime !== null && <span>耗时：{responseTime}ms</span>}
        </div>

        {/* 错误信息 */}
        {error && (
          <div className="result-box error">
            <strong>请求失败：</strong>{error}
            {error.includes('fetch') && (
              <p style={{ marginTop: '0.5rem' }}>
                提示：请确保 FastAPI 后端已在运行。（cd .. && uv run python step01_hello_fastapi.py）
              </p>
            )}
          </div>
        )}

        {/* 成功响应 */}
        {data && !error && (
          <div className="result-box">
            {JSON.stringify(data, null, 2)}
          </div>
        )}
      </div>

      {/* ========== 3. 请求状态管理原理 ========== */}
      <div className="learn-card">
        <h3>
          <span className="tag tag-advanced">进阶</span> 3. 请求三态管理 — loading | error | data
        </h3>
        <p style={{ marginBottom: '0.75rem', color: '#6b7280' }}>
          每个 API 调用都必须处理三种状态，这是前端开发的"黄金法则"。
          漏掉任何一种都会导致用户体验问题。
        </p>
        <div className="code-block">
{`// ===== 请求三态：缺一不可 =====
// 1. 加载中 → 显示骨架屏/加载动画
// 2. 成功   → 显示数据
// 3. 失败   → 显示错误提示 + 重试按钮

// 后端还没启动时前端请求 → 网络错误
// 网络错误 ≠ HTTP 错误（404/500），这是两个层面
// fetch 只把网络故障当异常（catch 捕获）
// HTTP 404/500 不走 catch，需要检查 response.ok

// ===== 标准的三态渲染模板 =====
function DataComponent() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchData()
      .then(setData)
      .catch(setError)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <Spinner />;          // 状态 1：加载中
  if (error) return <ErrorMessage error={error} />; // 状态 2：错误
  return <DataDisplay data={data} />;       // 状态 3：成功
}

// ===== 为什么三态缺一不可 =====
// 缺 loading → 用户看到空白页，不知道在加载
// 缺 error  → 加载失败后空白页，用户不知道出错了
// 缺 data   → 数据到了但没显示，白等了`}
        </div>
      </div>

      {/* ========== 4. 跨域问题 ========== */}
      <div className="learn-card">
        <h3>
          <span className="tag tag-advanced">进阶</span> 4. 跨域问题 (CORS) 与 Vite Proxy
        </h3>
        <p style={{ marginBottom: '0.75rem', color: '#6b7280' }}>
          浏览器不允许一个域名的页面请求另一个域名的 API（安全策略）。
          Vite proxy 在开发时绕过这个问题，生产环境由 Nginx 或 FastAPI CORS 中间件处理。
        </p>
        <div className="code-block">
{`// ===== 什么是跨域 (CORS)？=====
// 浏览器同源策略：协议 + 域名 + 端口 三者必须完全相同
// 前端 http://localhost:3000  请求  http://localhost:8000
// 端口不同 → 跨域！浏览器拦截请求

// ===== 开发环境解决方案：Vite Proxy =====
// vite.config.js 中配置：
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',  // FastAPI 地址
      changeOrigin: true,
    }
  }
}
// 效果：前端 fetch('/api/users') → Vite 接收 → 转发到 localhost:8000
// 浏览器看到的是同域请求，没有跨域问题

// ===== 生产环境解决方案 =====
// 方案 1：FastAPI 开启 CORS（见 step20_cors_security.py）
// 方案 2：Nginx 反向代理（前后端同一域名）
// 方案 3：FastAPI 直接 serve 编译好的 React 静态文件`}
        </div>
      </div>
    </div>
  );
}
