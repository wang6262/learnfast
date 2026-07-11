/**
 * ==============================================
 * 文件名：api.js
 * 【基础功能】封装 fetch 请求，统一管理所有后端 API 调用
 * 【核心学习知识点】
 *   1. fetch API — 浏览器原生 HTTP 请求方法（不依赖 axios）
 *   2. async/await — 异步请求的标准写法
 *   3. 统一错误处理 — 不用在每个组件里重复写 try/catch
 *   4. 请求拦截思想 — 统一处理响应状态码、错误提示
 * 【适用场景】任何需要调用后端 API 的前端项目
 * 【进阶说明】
 *   Base URL 管理：开发时通过 Vite proxy 转发，生产时由 Nginx/FastAPI 处理
 *   如果不用 proxy，需要写完整 URL：http://localhost:8000/api/users
 *   用 proxy 后只需要写相对路径：/api/users → Vite 自动转发
 *   同场景替代库：axios（功能更多，但需要额外安装）
 * ==============================================
 */

// ==============================================
// 配置：后端 API 基础地址
// 【基础】空字符串 = 用相对路径请求 → Vite proxy 转发到 FastAPI
// 【进阶】生产环境可改为完整 URL，或通过环境变量 import.meta.env.VITE_API_BASE 动态配置
//   环境变量文件：.env 文件中写 VITE_API_BASE=http://your-server.com
//   Vite 要求环境变量以 VITE_ 开头，才能在前端代码中访问
// ==============================================
const API_BASE = '/api';

// ==============================================
// 核心请求函数
// 【基础】封装了 fetch 请求的三大步骤：发请求 → 读响应 → 处理错误
// 【进阶】统一错误处理模式（类似后端的异常中间件）
//   1. HTTP 状态码异常（404、500）→ 自动抛出中文错误
//   2. 网络连接异常 → 提示检查后端是否启动
//   3. 响应体为空（204 No Content）→ 返回 null
// ==============================================
async function request(url, options = {}) {
  // Step 1：拼接完整 URL + 发送请求
  // 【基础】fetch 是浏览器内置的 HTTP 请求函数，返回 Promise
  //   Promise 是 JS 的异步编程方案，类似 Python 的 asyncio Future
  const fullUrl = API_BASE + url;
  const response = await fetch(fullUrl, {
    headers: {
      'Content-Type': 'application/json', // 告诉后端：我发的是 JSON 数据
      ...options.headers, // 合并调用者传入的额外请求头
    },
    ...options, // 合并 method、body 等参数
  });

  // Step 2：处理 HTTP 错误状态码
  // 【基础】fetch 不会自动为 404/500 报错，必须手动检查 response.ok
  //   这个设计很容易让新手踩坑！
  //   response.ok → true 表示 200-299，false 表示 4xx/5xx
  if (!response.ok) {
    // 尝试从响应中读取后端返回的错误详情
    const errorBody = await response.json().catch(() => ({}));
    // 抛出错误，带上 HTTP 状态码，方便调试
    throw new Error(errorBody.detail || `请求失败 (HTTP ${response.status})`);
  }

  // Step 3：解析 JSON 响应体
  // 204 No Content（删除操作常见）→ 没有响应体，返回 null
  if (response.status === 204) return null;

  return await response.json();
}

// ==============================================
// API 方法集合
// 【基础】按 HTTP 方法分类封装，调用时只需要传路径和数据
//
// 【学习知识点】export 导出 vs export default 导出
//   export const → 按名称导入：import { get } from './api.js'
//   export default → 可以随意命名导入：import xxx from './api.js'
//   这里用具名导出，因为调用时更清晰：api.get() / api.post()
// ==============================================

// GET 请求 — 获取数据（列表、详情）
export function get(url) {
  return request(url, { method: 'GET' });
}

// POST 请求 — 创建新数据（新增用户、登录）
export function post(url, data) {
  return request(url, {
    method: 'POST',
    body: JSON.stringify(data), // 【基础】JS 对象 → JSON 字符串，如 {name:"张三"} → '{"name":"张三"}'
  });
}

// PUT 请求 — 完整更新数据（替换整个对象）
export function put(url, data) {
  return request(url, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

// PATCH 请求 — 部分更新数据（只改一两个字段）
export function patch(url, data) {
  return request(url, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

// DELETE 请求 — 删除数据
export function del(url) {
  return request(url, { method: 'DELETE' });
}

// 【学习知识点】具名导出 put vs 默认导出
// 这里 put 是函数名，和 HTTP PUT 方法同名，容易混淆
// 实际开发中常用 axios 库，提供 api.get() / api.post() 方法，更直观
// 这里先手写，帮助理解 fetch 原理，后续可替换为 axios
