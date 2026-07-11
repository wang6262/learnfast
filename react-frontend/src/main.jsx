/**
 * ==============================================
 * 文件名：main.jsx
 * 【基础功能】React 应用入口，负责把 App 组件挂载到 HTML 页面上
 * 【核心学习知识点】
 *   1. React 入口文件的标准写法
 *   2. createRoot — React 18 新渲染 API（替代旧版 ReactDOM.render）
 *   3. StrictMode — 开发模式下的严格检查，帮你发现潜在问题
 * 【适用场景】每个 React 项目必有
 * 【运行方式】npm run dev → 浏览器访问 http://localhost:3000
 * 【进阶说明】
 *   1. createRoot 支持并发渲染 (Concurrent Mode)，比旧 API 更快
 *   2. StrictMode 会故意执行两次 useEffect，用于检测副作用是否正确清理
 *   3. import "file.css" 是 Vite 的特性，原生 JS 不支持直接导入 CSS
 * ==============================================
 */
import React from 'react';
import ReactDOM from 'react-dom/client';

// 【基础】导入 App 组件 — ./ 表示当前目录，.jsx 可以省略
import App from './App';

// 【基础】导入全局样式 — Vite 支持 JS 中直接 import CSS
import './App.css';

// ==============================================
// 步骤 1：获取 HTML 中的根元素
// 【基础】index.html 中 <div id="root"></div> 就是 React 的"画布"
// ==============================================
const rootElement = document.getElementById('root');

// ==============================================
// 步骤 2：创建 React 根节点 (React 18 新写法)
// 【基础】createRoot 创建一个 React 渲染入口
// 【进阶】React 18 的 createRoot 替代了 React 17 的 ReactDOM.render
//   优点：支持并发渲染、自动批处理、Suspense 改进
//   旧写法：ReactDOM.render(<App />, document.getElementById('root'))
// ==============================================
const root = ReactDOM.createRoot(rootElement);

// ==============================================
// 步骤 3：渲染 App 组件到页面上
// 【基础】root.render() 把 React 组件变成真实 DOM 显示在浏览器中
// StrictMode 包裹：开发环境会额外检查代码问题（控制台会有警告/提示）
//   生产环境 StrictMode 不生效，不影响性能
// ==============================================
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
