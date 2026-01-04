<!-- 登录页面：处理用户认证（邮箱/密码、错误反馈、成功后跳转）。 -->
 <template>
    <div class="auth-container">
        <el-card class="auth-card">
            <div class="auth-title">ELECTRICITY SYSTEM</div>
            <el-tabs v-model="activeTab" class="auth-tabs">
                <el-tab-pane label="登录" name="login">
                    <el-form :model="loginForm" ref="loginFormRef" class="login-form">
                        <el-form-item label="邮箱" prop="mail">
                            <el-input v-model="loginForm.mail" autocomplete="off"></el-input>
                        </el-form-item>
                        <el-form-item label="密码" prop="password">
                            <el-input type="password" v-model="loginForm.password" autocomplete="off"></el-input>
                        </el-form-item>
                        <el-form-item>
                            <el-button type="primary" @click="handleLogin" style="width: 100%;">登录</el-button>
                        </el-form-item>
                        <div class="forgot-password">
                            <el-link type="primary" @click="showResetDialog = true">忘记密码？</el-link>
                        </div>
                    </el-form>
                </el-tab-pane>
                <el-tab-pane label="注册" name="register">
                    <el-form class="register-form">
                        <el-form-item label="邮箱" prop="mail">
                            <el-input v-model="registerForm.mail" autocomplete="off"></el-input>
                        </el-form-item>
                        <el-form-item label="密码" prop="password">
                            <el-input type="password" v-model="registerForm.password" autocomplete="off"></el-input>
                        </el-form-item>
                        <el-form-item label="确认密码" prop="confirm_password">
                            <el-input type="password" v-model="confirmPassword" autocomplete="off"></el-input>
                        </el-form-item>
                        <el-form-item label="姓名" prop="username">
                            <el-input v-model="registerForm.username" placeholder="选填，2-20个字符" autocomplete="off"></el-input>
                        </el-form-item>
                        <el-form-item label="身份证号" prop="id_card">
                            <el-input v-model="registerForm.id_card" placeholder="选填，15或18位身份证号" autocomplete="off"></el-input>
                        </el-form-item>
                        <el-form-item label="地区ID" prop="region_id">
                            <el-input v-model.number="registerForm.region_id" type="number" placeholder="必填，请输入片区编号" autocomplete="off"></el-input>
                        </el-form-item>
                        <el-button type="primary" @click="handleRegister">注册</el-button>
                    </el-form>
                </el-tab-pane>
            </el-tabs>
        </el-card>
        
        <!-- 重置密码对话框 -->
        <el-dialog 
            v-model="showResetDialog" 
            title="重置密码" 
            width="400px"
            :close-on-click-modal="false"
        >
            <el-form :model="resetForm" label-width="80px">
                <el-form-item label="邮箱">
                    <el-input 
                        v-model="resetForm.mail" 
                        placeholder="请输入注册邮箱"
                        :disabled="resetStep === 2"
                    ></el-input>
                </el-form-item>
                
                <el-form-item label="验证码" v-if="resetStep === 2">
                    <div style="display: flex; gap: 10px;">
                        <el-input 
                            v-model="resetForm.code" 
                            placeholder="请输入6位验证码"
                            maxlength="6"
                            style="flex: 1;"
                        ></el-input>
                        <el-button 
                            @click="handleSendCode" 
                            :disabled="countdown > 0"
                            style="width: 100px;"
                        >
                            {{ countdown > 0 ? `${countdown}秒` : '重新发送' }}
                        </el-button>
                    </div>
                </el-form-item>
                
                <el-form-item label="新密码" v-if="resetStep === 2">
                    <el-input 
                        type="password" 
                        v-model="resetForm.new_password" 
                        placeholder="请输入新密码（6-20位）"
                    ></el-input>
                </el-form-item>
                
                <el-form-item label="确认密码" v-if="resetStep === 2">
                    <el-input 
                        type="password" 
                        v-model="resetForm.confirm_password" 
                        placeholder="请再次输入新密码"
                    ></el-input>
                </el-form-item>
            </el-form>
            
            <template #footer>
                <span class="dialog-footer">
                    <el-button @click="handleCancelReset">取消</el-button>
                    <el-button 
                        type="primary" 
                        @click="resetStep === 1 ? handleSendCode() : handleResetPassword()"
                        :loading="resetLoading"
                    >
                        {{ resetStep === 1 ? '发送验证码' : '重置密码' }}
                    </el-button>
                </span>
            </template>
        </el-dialog>
    </div>
 </template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuth } from '@/composables/useAuth'
import userApi from '@/services/api/user'

const router = useRouter()
const { signIn } = useAuth()
const activeTab = ref('login')
const loginFormRef = ref(null)
const loginForm = ref({
  mail: '',
  password: ''
})
const registerForm = ref({
  mail: '',
  password: '',
  username: '',
  id_card: '',
  region_id: undefined as number | undefined
})
const confirmPassword = ref('')

// 重置密码相关
const showResetDialog = ref(false)
const resetStep = ref(1) // 1: 输入邮箱, 2: 输入验证码和新密码
const resetLoading = ref(false)
const countdown = ref(0)
const resetForm = ref({
  mail: '',
  code: '',
  new_password: '',
  confirm_password: ''
})

let countdownTimer: number | null = null

// 发送验证码
const handleSendCode = async () => {
  if (!resetForm.value.mail) {
    ElMessage.error('请输入邮箱地址')
    return
  }
  
  // 验证邮箱格式
  const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/
  if (!emailRegex.test(resetForm.value.mail)) {
    ElMessage.error('请输入有效的邮箱地址')
    return
  }
  
  resetLoading.value = true
  try {
    const response = await userApi.sendResetCode({
      mail: resetForm.value.mail
    })
    
    if (response.data.success) {
      ElMessage.success('验证码已发送到您的邮箱，请注意查收')
      resetStep.value = 2
      
      // 开始倒计时
      countdown.value = 60
      if (countdownTimer) clearInterval(countdownTimer)
      countdownTimer = setInterval(() => {
        countdown.value--
        if (countdown.value <= 0) {
          if (countdownTimer) clearInterval(countdownTimer)
        }
      }, 1000)
    } else {
      ElMessage.error(response.data.message || '发送验证码失败')
    }
  } catch (error: any) {
    ElMessage.error(error.message || '发送验证码请求失败')
    console.error('Send reset code error:', error)
  } finally {
    resetLoading.value = false
  }
}

// 重置密码
const handleResetPassword = async () => {
  if (!resetForm.value.code) {
    ElMessage.error('请输入验证码')
    return
  }
  
  if (!resetForm.value.new_password) {
    ElMessage.error('请输入新密码')
    return
  }
  
  if (resetForm.value.new_password.length < 6 || resetForm.value.new_password.length > 20) {
    ElMessage.error('密码长度应为6-20位')
    return
  }
  
  if (resetForm.value.new_password !== resetForm.value.confirm_password) {
    ElMessage.error('两次输入的密码不一致')
    return
  }
  
  resetLoading.value = true
  try {
    const response = await userApi.resetPassword({
      mail: resetForm.value.mail,
      code: resetForm.value.code,
      new_password: resetForm.value.new_password
    })
    
    if (response.data.success) {
      ElMessage.success('密码重置成功，请使用新密码登录')
      handleCancelReset()
      // 切换到登录标签
      activeTab.value = 'login'
    } else {
      ElMessage.error(response.data.message || '密码重置失败')
    }
  } catch (error: any) {
    ElMessage.error(error.message || '密码重置请求失败')
    console.error('Reset password error:', error)
  } finally {
    resetLoading.value = false
  }
}

// 取消重置密码
const handleCancelReset = () => {
  showResetDialog.value = false
  resetStep.value = 1
  countdown.value = 0
  if (countdownTimer) {
    clearInterval(countdownTimer)
    countdownTimer = null
  }
  resetForm.value = {
    mail: '',
    code: '',
    new_password: '',
    confirm_password: ''
  }
}

const handleLogin = async () => {
  // 前端表单验证
  if (!loginForm.value.mail) {
    ElMessage.warning('📧 请输入邮箱地址')
    return
  }
  
  if (!loginForm.value.password) {
    ElMessage.warning('🔒 请输入密码')
    return
  }
  
  // 邮箱格式简单验证
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!emailRegex.test(loginForm.value.mail)) {
    ElMessage.warning('⚠️ 请输入有效的邮箱地址')
    return
  }
  
  try {
    console.log('开始登录...')
    const result = await signIn({
      mail: loginForm.value.mail,
      password: loginForm.value.password
    })
    console.log('登录结果:', result)
    ElMessage.success('✅ 登录成功！')
    console.log('准备跳转到 /dashboard')
    await router.push('/dashboard')
    console.log('跳转完成')
  } catch (error: any) {
    console.error('登录错误:', error)
    
    // 提取错误信息，根据不同的错误类型显示不同的提示
    let errorMessage = '登录失败，请稍后重试'
    
    // 检查是否是401错误（密码错误或账号不存在）
    if (error.response?.status === 401) {
      errorMessage = '邮箱或密码错误，请重新输入'
    } else if (error.message && !error.message.includes('status code')) {
      // 使用后端返回的具体错误信息（排除技术性错误）
      errorMessage = error.message
    } else if (error.response?.data?.message) {
      errorMessage = error.response.data.message
    }
    
    // 根据常见错误类型给出更友好的提示
    if (errorMessage.includes('邮箱') || errorMessage.includes('密码') || errorMessage.includes('错误')) {
      ElMessage.error(`⚠️ ${errorMessage}`)
    } else if (errorMessage.includes('不存在')) {
      ElMessage.error('🚫 该账号不存在，请检查邮箱地址')
    } else if (error.response?.status === 401) {
      ElMessage.error('⚠️ 邮箱或密码错误，请重新输入')
    } else {
      ElMessage.error(`❌ ${errorMessage}`)
    }
    
    console.error('Login error:', error)
  }
}

const handleRegister = async () => {
  try {
    if (registerForm.value.password !== confirmPassword.value) {
      ElMessage.error('⚠️ 两次输入的密码不一致')
      return
    }
    
    if (!registerForm.value.region_id) {
      ElMessage.error('⚠️ 请输入地区ID')
      return
    }
    
    const response = await userApi.register({
      mail: registerForm.value.mail,
      password: registerForm.value.password,
      real_name: registerForm.value.username,
      idcard: registerForm.value.id_card,
      region_id: registerForm.value.region_id
    })
    
    if (response.success) {
      ElMessage.success('✅ 注册成功！请登录')
      // 重置表单
      registerForm.value = {
        mail: '',
        password: '',
        username: '',
        id_card: '',
        region_id: undefined
      }
      confirmPassword.value = ''
      activeTab.value = 'login'
    } else {
      ElMessage.error(`❌ ${response.message || '注册失败'}`)
    }
  } catch (error: any) {
    // 显示详细的错误信息
    let errorMsg = '注册请求出错'
    
    if (error.message) {
      errorMsg = error.message
    } else if (error.response?.data?.message) {
      errorMsg = error.response.data.message
    }
    
    // 根据常见错误类型给出更友好的提示
    if (errorMsg.includes('已存在') || errorMsg.includes('已注册')) {
      ElMessage.error('🚫 该邮箱已被注册，请直接登录或使用其他邮箱')
    } else if (errorMsg.includes('格式')) {
      ElMessage.error(`⚠️ ${errorMsg}`)
    } else {
      ElMessage.error(`❌ ${errorMsg}`)
    }
    
    console.error('Register error:', error)
  }
}

</script>

<style scoped>
.auth-container {
  min-height: 100vh;
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background-image: url('@/assets/images/flowers.jpg') !important;
  background-size: cover !important;
  background-position: center !important;
  background-repeat: no-repeat !important;
  background-attachment: fixed !important;
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  overflow-y: auto;
}

.auth-container::before {
  content: '';
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.3);
  z-index: 1;
}

.auth-card {
  position: relative;
  z-index: 2;
  width: 100%;
  max-width: 450px;
  margin: 20px;
  backdrop-filter: blur(10px);
  background-color: rgba(255, 255, 255, 0.95) !important;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  border-radius: 16px;
}

.auth-title {
  font-size: 28px;
  font-weight: bold;
  text-align: center;
  margin-bottom: 24px;
  color: #2c3e50;
  letter-spacing: 2px;
}

.auth-tabs {
  margin-top: 16px;
}

.login-form,
.register-form {
  margin-top: 20px;
}

.forgot-password {
  text-align: right;
  margin-top: -10px;
  margin-bottom: 10px;
}

:deep(.el-dialog) {
  border-radius: 12px;
}

:deep(.el-dialog__header) {
  border-bottom: 1px solid #eee;
  padding-bottom: 15px;
}

:deep(.el-dialog__body) {
  padding: 25px 20px;
}
</style>