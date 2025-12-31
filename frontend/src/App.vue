<script setup lang="ts">
// App.vue: 应用根组件
// 职责：全局布局容器、路由出口、样式导入

import { RouterView } from 'vue-router'
// TODO: 导入 Header 与 Sidebar（如需全局展示）
// TODO: 导入全局状态管理（如主题、用户信息）
</script>

<template>
  <!-- 路由出口：所有页面在此渲染 -->
  <RouterView />
</template>

<style>
/* 导入全局样式与主题变量 */
@import './styles/variables.css';
@import './styles/globals.css';
@import './styles/components.css';
</style>
