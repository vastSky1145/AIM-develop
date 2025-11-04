<template>
  <div>
    <h1>关于页面</h1>
    <p>这是一个使用Vue Router的示例应用。</p>
    <nav>
      <router-link to="/">首页</router-link> |
      <router-link to="/about">关于</router-link>
    </nav>
  </div>
</template>

<script setup>
// 关于页面组件逻辑
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
