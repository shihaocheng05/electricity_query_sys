<template>
  <div class="auth-layout">
    <div class="auth-layout__background"></div>
    <div class="auth-layout__container">
      <div class="auth-layout__card">
        <div class="auth-layout__logo">
          <h1>⚡ 电费查询系统</h1>
          <p>Electricity Bill Management System</p>
        </div>
        <RouterView />
      </div>
      <footer class="auth-layout__footer">
        <p>&copy; 2024 电费查询系统. All rights reserved.</p>
      </footer>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '@/composables/useAuth'

const router = useRouter()
const { isLoggedIn, initAuth } = useAuth()

onMounted(async () => {
  await initAuth()
  if (isLoggedIn.value) {
    router.push('/dashboard')
  }
})
</script>

<style scoped>
.auth-layout {
  position: relative;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.auth-layout__background {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-image: 
    radial-gradient(circle at 20% 50%, rgba(255, 255, 255, 0.1) 0%, transparent 50%),
    radial-gradient(circle at 80% 80%, rgba(255, 255, 255, 0.15) 0%, transparent 50%);
  animation: float 20s ease-in-out infinite;
}

@keyframes float {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-20px);
  }
}

.auth-layout__container {
  position: relative;
  width: 100%;
  max-width: 420px;
  padding: 20px;
}

.auth-layout__card {
  background: white;
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  padding: 40px;
  animation: slideUp 0.5s ease-out;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.auth-layout__logo {
  text-align: center;
  margin-bottom: 32px;
}

.auth-layout__logo h1 {
  font-size: 28px;
  font-weight: 700;
  color: #333;
  margin: 0 0 8px 0;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.auth-layout__logo p {
  font-size: 14px;
  color: #999;
  margin: 0;
  font-weight: 400;
}

.auth-layout__footer {
  text-align: center;
  margin-top: 24px;
  color: rgba(255, 255, 255, 0.8);
  font-size: 14px;
}

.auth-layout__footer p {
  margin: 0;
}

@media (max-width: 480px) {
  .auth-layout__container {
    padding: 16px;
  }
  
  .auth-layout__card {
    padding: 24px;
  }
  
  .auth-layout__logo h1 {
    font-size: 24px;
  }
}
</style>
