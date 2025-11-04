<template>
  <div>
    <h1>首页</h1>
    <p>欢迎来到我的Vue应用！</p>
    <nav>
      <router-link to="/">首页</router-link> |
      <router-link to="/about">关于</router-link>
    </nav>
  </div>
</template>

<script setup>
// 首页组件逻辑
</script>

<style scoped>
nav {
  margin-top: 20px;
}

.router-link-active {
  font-weight: bold;
  color: #42b883;
}
</style>
