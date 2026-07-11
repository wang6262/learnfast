/**
 * ==============================================
 * 文件名：App.jsx
 * 【基础功能】React 应用的主组件，包含学习步骤的导航切换
 * 【核心学习知识点】
 *   1. useState — 管理当前选中的学习步骤
 *   2. 条件渲染 — 根据当前步骤显示不同内容
 *   3. 组件化思想 — 每个步骤独立成组件，互不影响
 *   4. 事件处理 — 点击按钮切换步骤
 * 【适用场景】学习导航 / 标签页切换 / 分步表单
 * 【进阶说明】这里未使用 react-router，用简单的状态切换实现导航，减少入门难度
 * ==============================================
 */
import React, { useState } from 'react';

// 【基础】导入各个学习步骤组件
// 每个组件是一个 .jsx 文件，默认导出组件函数
import Step01_JSX from './components/Step01_JSX';
import Step02_State from './components/Step02_State';
import Step03_Props from './components/Step03_Props';
import Step04_Events from './components/Step04_Events';
import Step05_Effects from './components/Step05_Effects';
import Step06_Fetch from './components/Step06_Fetch';
import Step07_CRUD from './components/Step07_CRUD';

// ==============================================
// 步骤列表配置
// 【基础】把每个步骤的信息集中放在数组里，方便统一管理
//   修改/新增步骤只需要改这个数组，不用改 JSX 模板部分
// 【进阶】这种"数据驱动渲染"是 React 的核心理念
//   数据变 → UI 自动变，不需要手动操作 DOM
// ==============================================
const STEPS = [
  { id: 1, name: 'JSX 基础',     component: Step01_JSX },
  { id: 2, name: 'useState 状态', component: Step02_State },
  { id: 3, name: 'Props 传参',    component: Step03_Props },
  { id: 4, name: '事件 & 表单',   component: Step04_Events },
  { id: 5, name: 'useEffect',     component: Step05_Effects },
  { id: 6, name: '调用 API',      component: Step06_Fetch },
  { id: 7, name: 'CRUD 实战',     component: Step07_CRUD },
];

export default function App() {
  // ==============================================
  // 状态：当前显示哪个步骤（默认显示步骤 1）
  // 【基础】useState 返回 [当前值, 修改函数]
  //   useState(1) 的 1 是初始值，页面加载默认显示步骤 1
  // 【进阶】React 18 的自动批处理：多次 setActiveStep 只会渲染一次
  //   不需要像旧版本手动优化
  // ==============================================
  const [activeStep, setActiveStep] = useState(1);

  // 找到当前激活的步骤对象（用于获取组件和名称）
  const currentStep = STEPS.find((s) => s.id === activeStep);

  // ==============================================
  // 渲染 UI
  // 【基础】JSX 语法规则：
  //   1. {} 里可以放 JS 变量/表达式
  //   2. className 就是 HTML 的 class（class 是 JS 保留字，所以改名）
  //   3. 事件用驼峰命名：onClick（HTML 是 onclick，全小写）
  //   4. 最外层必须有且仅有一个根元素（这里用 <></> 空标签包裹）
  //   5. 空标签 <>...</> 是 <React.Fragment> 的简写
  //   6. style={{}} — 外层 {} 是 JSX 变量语法，内层 {} 是 JS 对象字面量
  // ==============================================
  return (
    <>
      {/* ========== 顶部标题栏 ========== */}
      <header className="app-header">
        <h1>LearnFast React — React 从零到实战</h1>
        <p className="app-subtitle">配套 FastAPI 后端，逐步学习 React 核心概念</p>
      </header>

      {/* ========== 步骤导航栏 ========== */}
      {/* 【基础】用 .map() 遍历数组生成按钮列表 */}
      <nav className="step-nav">
        {STEPS.map((step) => (
          <button
            key={step.id}
            className={`step-btn ${activeStep === step.id ? 'active' : ''}`}
            onClick={() => setActiveStep(step.id)}
          >
            <span className="step-number">Step {step.id}</span>
            <span className="step-name">{step.name}</span>
          </button>
        ))}
      </nav>

      {/* ========== 内容区域 ========== */}
      {/* 【基础】条件渲染：根据当前步骤显示对应的组件 */}
      <main className="step-content">
        <h2 className="step-title">
          Step {currentStep.id}：{currentStep.name}
        </h2>
        {React.createElement(currentStep.component)}
      </main>
    </>
  );
}
