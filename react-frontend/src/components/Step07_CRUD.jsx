/**
 * ==============================================
 * 文件名：Step07_CRUD.jsx
 * 【基础功能】React + FastAPI 完整 CRUD 实战 — 用户管理系统
 * 【核心学习知识点】
 *   1. 完整 CRUD 流程 — Create / Read / Update / Delete
 *   2. 前后端协作模式 — 前端 UI + 后端 API 的分工配合
 *   3. 乐观更新 — 先更新 UI 再确认后端（提升响应速度）
 *   4. 表单校验 — 提交前校验 + 后端错误展示
 *   5. 用户交互细节 — 确认对话框、加载状态、错误回滚
 *   6. 列表/详情视图切换 — 多视图数据管理
 * 【适用场景】管理后台、数据面板、任何需要数据操作的页面
 * 【前置条件】FastAPI 后端在 localhost:8000 运行
 * 【进阶说明】
 *   实际项目中 CRUD 会配合以下技术：
 *   1. React Query — 自动缓存失效、后台刷新
 *   2. React Hook Form — 表单校验库
 *   3. Zod — 前后端共享 schema 校验
 *   4. react-router — 列表/详情分页路由
 * ==============================================
 */
import React, { useState, useEffect, useCallback } from 'react';
import * as api from '../api'; // 使用封装的 API 模块

// ==============================================
// 子组件：用户表单（创建 + 编辑复用同一表单）
// 【进阶】通过 initialData 区分创建/编辑模式
//   有 initialData → 编辑模式（预填数据）
//   无 initialData → 创建模式（空表单）
// ==============================================
function UserForm({ initialData, onSubmit, onCancel, loading }) {
  const [form, setForm] = useState({
    username: initialData?.username || '',
    email: initialData?.email || '',
    full_name: initialData?.full_name || '',
    password: '', // 编辑时可选填密码
  });
  const [errors, setErrors] = useState({});

  const isEdit = !!initialData; // !! 转换为布尔值

  function handleChange(e) {
    const { name, value } = e.target;
    setForm({ ...form, [name]: value });
    // 用户修改后清除对应字段的错误
    if (errors[name]) setErrors({ ...errors, [name]: '' });
  }

  // 前端校验（提交前检查）
  function validate() {
    const errs = {};
    if (!form.username.trim()) errs.username = '用户名不能为空';
    if (form.username.length < 2) errs.username = '用户名至少 2 个字符';
    if (!form.email.trim()) errs.email = '邮箱不能为空';
    else if (!form.email.includes('@')) errs.email = '邮箱格式不正确';
    if (!isEdit && !form.password) errs.password = '创建用户需要设置密码';
    setErrors(errs);
    return Object.keys(errs).length === 0; // 没有错误 → 校验通过
  }

  function handleSubmit(e) {
    e.preventDefault();
    if (!validate()) return;

    // 构造提交数据：编辑时不传空密码
    const payload = { ...form };
    if (isEdit && !payload.password) delete payload.password;

    onSubmit(payload);
  }

  return (
    <form onSubmit={handleSubmit}>
      <div className="grid-2col">
        <div className="form-group">
          <label>用户名 *</label>
          <input className="input" name="username" value={form.username} onChange={handleChange} placeholder="至少2个字符" />
          {errors.username && <span style={{ color: '#dc2626', fontSize: '0.75rem' }}>{errors.username}</span>}
        </div>
        <div className="form-group">
          <label>邮箱 *</label>
          <input className="input" name="email" type="email" value={form.email} onChange={handleChange} placeholder="user@mail.com" />
          {errors.email && <span style={{ color: '#dc2626', fontSize: '0.75rem' }}>{errors.email}</span>}
        </div>
      </div>
      <div className="form-group">
        <label>全名</label>
        <input className="input" name="full_name" value={form.full_name} onChange={handleChange} placeholder="选填" />
      </div>
      <div className="form-group">
        <label>密码 {isEdit ? '(留空则不修改)' : '*'}</label>
        <input className="input" name="password" type="password" value={form.password} onChange={handleChange} placeholder={isEdit ? '留空则不修改' : '请输入密码'} />
        {errors.password && <span style={{ color: '#dc2626', fontSize: '0.75rem' }}>{errors.password}</span>}
      </div>
      <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.75rem' }}>
        <button className="btn btn-primary" type="submit" disabled={loading}>
          {loading ? '提交中...' : (isEdit ? '保存修改' : '创建用户')}
        </button>
        <button className="btn" type="button" style={{ background: '#e5e7eb' }} onClick={onCancel}>
          取消
        </button>
      </div>
    </form>
  );
}

export default function Step07_CRUD() {
  // ==============================================
  // 状态管理
  // ==============================================
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showForm, setShowForm] = useState(false);    // 是否显示表单
  const [editingUser, setEditingUser] = useState(null); // 正在编辑的用户
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState(null); // 操作成功提示

  // ==============================================
  // 加载用户列表（Read 操作）
  // 【基础】useEffect 在组件挂载时从后端获取数据
  // ==============================================
  const loadUsers = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.get('/users/');
      setUsers(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadUsers();
  }, [loadUsers]);

  // ==============================================
  // 创建用户（Create 操作）
  // ==============================================
  async function handleCreate(payload) {
    setSubmitting(true);
    try {
      const newUser = await api.post('/users/', payload);
      // 【进阶】乐观更新：后端成功后直接添加到列表头部
      setUsers((prev) => [newUser, ...prev]);
      setShowForm(false);
      setMessage({ type: 'success', text: `用户 "${newUser.username}" 创建成功` });
    } catch (err) {
      setMessage({ type: 'error', text: err.message });
    } finally {
      setSubmitting(false);
    }
  }

  // ==============================================
  // 更新用户（Update 操作）
  // ==============================================
  async function handleUpdate(payload) {
    setSubmitting(true);
    try {
      const updated = await api.put(`/users/${editingUser.id}`, payload);
      // 更新列表中的对应项
      setUsers((prev) => prev.map((u) => (u.id === updated.id ? updated : u)));
      setEditingUser(null);
      setMessage({ type: 'success', text: `用户 "${updated.username}" 更新成功` });
    } catch (err) {
      setMessage({ type: 'error', text: err.message });
    } finally {
      setSubmitting(false);
    }
  }

  // ==============================================
  // 删除用户（Delete 操作）
  // ==============================================
  async function handleDelete(user) {
    // 【基础】确认对话框，防止误删
    if (!window.confirm(`确定要删除用户 "${user.username}" 吗？此操作不可撤销。`)) return;

    // 【进阶】乐观删除：先移除 UI，再等后端确认
    setUsers((prev) => prev.filter((u) => u.id !== user.id));
    try {
      await api.del(`/users/${user.id}`);
      setMessage({ type: 'success', text: `用户 "${user.username}" 已删除` });
    } catch (err) {
      // 删除失败 → 重新加载列表恢复数据
      setMessage({ type: 'error', text: '删除失败：' + err.message });
      loadUsers();
    }
  }

  // ==============================================
  // 自动清除提示消息（3 秒后消失）
  // ==============================================
  useEffect(() => {
    if (message) {
      const timer = setTimeout(() => setMessage(null), 3000);
      return () => clearTimeout(timer);
    }
  }, [message]);

  return (
    <div>
      {/* ========== 操作按钮栏 ========== */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <h3 style={{ margin: 0 }}>
          <span className="tag tag-basic">基础</span> 用户数据管理 (CRUD)
        </h3>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          {!showForm && !editingUser && (
            <button className="btn btn-primary" onClick={() => setShowForm(true)}>
              + 新建用户
            </button>
          )}
          <button className="btn" style={{ background: '#e5e7eb' }} onClick={loadUsers} disabled={loading}>
            {loading ? '加载中...' : '刷新列表'}
          </button>
        </div>
      </div>

      {/* ========== 提示消息 ========== */}
      {message && (
        <div className={`result-box ${message.type === 'error' ? 'error' : ''}`} style={{ marginBottom: '1rem' }}>
          {message.type === 'success' ? '✅ ' : '❌ '}
          {message.text}
        </div>
      )}

      {/* ========== 创建表单 ========== */}
      {showForm && (
        <div className="learn-card">
          <h4>创建新用户</h4>
          <UserForm onSubmit={handleCreate} onCancel={() => setShowForm(false)} loading={submitting} />
        </div>
      )}

      {/* ========== 编辑表单 ========== */}
      {editingUser && (
        <div className="learn-card">
          <h4>编辑用户：{editingUser.username}</h4>
          <UserForm initialData={editingUser} onSubmit={handleUpdate} onCancel={() => setEditingUser(null)} loading={submitting} />
        </div>
      )}

      {/* ========== 用户列表表格 ========== */}
      <div className="learn-card">
        {loading ? (
          <p style={{ textAlign: 'center', color: '#6b7280', padding: '2rem' }}>⏳ 正在加载用户列表...</p>
        ) : error ? (
          <div className="result-box error">
            <strong>加载失败：</strong>{error}
            <p style={{ marginTop: '0.5rem' }}>请确认 FastAPI 后端已启动：uv run python step01_hello_fastapi.py</p>
            <button className="btn btn-primary" style={{ marginTop: '0.5rem' }} onClick={loadUsers}>重试</button>
          </div>
        ) : users.length === 0 ? (
          <p style={{ textAlign: 'center', color: '#6b7280', padding: '2rem' }}>
            暂无用户数据，点击"新建用户"添加
          </p>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>用户名</th>
                <th>邮箱</th>
                <th>全名</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              {users.map((user) => (
                <tr key={user.id}>
                  <td>{user.id}</td>
                  <td><strong>{user.username}</strong></td>
                  <td>{user.email}</td>
                  <td>{user.full_name || '-'}</td>
                  <td>
                    <button
                      className="btn btn-primary"
                      style={{ padding: '0.25rem 0.5rem', fontSize: '0.8rem', marginRight: '0.25rem' }}
                      onClick={() => setEditingUser(user)}
                    >
                      编辑
                    </button>
                    <button
                      className="btn btn-danger"
                      style={{ padding: '0.25rem 0.5rem', fontSize: '0.8rem' }}
                      onClick={() => handleDelete(user)}
                    >
                      删除
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        <p style={{ fontSize: '0.8rem', color: '#6b7280', marginTop: '0.5rem' }}>
          共 {users.length} 个用户
        </p>
      </div>

      {/* ========== CRUD 流程图 ========== */}
      <div className="learn-card">
        <h3>
          <span className="tag tag-advanced">进阶</span> 前后端 CRUD 协作流程
        </h3>
        <div className="code-block">
{`// ===== 前后端 CRUD 协作全景图 =====

// 前端 React                       后端 FastAPI
// ============                     ==============
//
// Create（创建）
// 表单填写 → 前端校验 → POST /api/users/ → Pydantic 校验
//     ↑                                        ↓
//     └──── 返回新用户 JSON ←── 存数据库 ←─────┘
// 列表头部插入新数据

// Read（读取）
// 页面加载 → GET /api/users/ → 查询数据库
//     ↑                          ↓
//     └──── 用户列表 JSON ←──────┘
// 渲染表格

// Update（更新）
// 点击"编辑" → 填表单 → PUT /api/users/{id} → 校验 + 更新
//     ↑                                            ↓
//     └────── 更新后的用户 JSON ←── 写数据库 ←──────┘
// 列表中找到对应项替换

// Delete（删除）
// 点击"删除" → 确认对话框 → DELETE /api/users/{id} → 删除记录
//     ↑                                                ↓
//     └──────── 204 No Content ←── 从数据库删除 ←──────┘
// 列表过滤掉该项

// ===== 关键原则 =====
// 1. 前端校验 + 后端校验（双重保障）
// 2. 乐观更新：先改 UI 再确认（快速响应）
// 3. 错误回滚：后端失败时恢复数据
// 4. 确认对话框：防止误删/重复提交`}
        </div>
      </div>
    </div>
  );
}
