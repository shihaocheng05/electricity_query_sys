<template>
  <div class="settings">
    <h1 class="settings__title">{{ isAdmin ? '系统设置' : '个人设置' }}</h1>

    <!-- 管理员：用户管理 -->
    <div v-if="isAdmin" class="settings__card">
      <h2 class="settings__card-title">用户管理</h2>
      <div class="user-management">
        <div class="user-search">
          <input 
            v-model="searchKeyword" 
            type="text" 
            placeholder="搜索用户（邮箱、姓名）"
            @keyup.enter="searchUsers"
          />
          <button class="settings__button" @click="searchUsers">搜索</button>
        </div>
        
        <div class="user-list">
          <table class="user-table">
            <thead>
              <tr>
                <th>用户ID</th>
                <th>邮箱</th>
                <th>姓名</th>
                <th>片区</th>
                <th>角色</th>
                <th>状态</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="user in userList" :key="user.user_id">
                <td>{{ user.user_id }}</td>
                <td>{{ user.mail }}</td>
                <td>{{ user.real_name || '未设置' }}</td>
                <td>{{ user.region_name || '未分配' }}</td>
                <td>
                  <span :class="getRoleClass(user.role)">
                    {{ getRoleLabel(user.role) }}
                  </span>
                </td>
                <td>{{ getStatusLabel(user.status) }}</td>
                <td>
                  <button class="action-btn" @click="editUser(user)">编辑</button>
                </td>
              </tr>
            </tbody>
          </table>
          
          <div v-if="userList.length === 0" class="empty-state">
            暂无用户数据
          </div>
          
          <div v-if="pagination.total > 0" class="pagination">
            <button @click="changePage(pagination.page - 1)" :disabled="pagination.page === 1">上一页</button>
            <span>第 {{ pagination.page }} / {{ pagination.pages }} 页</span>
            <button @click="changePage(pagination.page + 1)" :disabled="!pagination.has_next">下一页</button>
          </div>
        </div>
      </div>
    </div>

    <!-- 用户信息卡片 -->
    <div class="settings__card">
      <h2 class="settings__card-title">基本信息</h2>
      <div class="settings__form">
        <div class="settings__form-item">
          <label>邮箱</label>
          <input v-model="userInfo.mail" type="email" :disabled="!isEditing" />
        </div>
        <div class="settings__form-item">
          <label>真实姓名</label>
          <input v-model="userInfo.real_name" type="text" :disabled="!isEditing" />
        </div>
        <div class="settings__form-item">
          <label>身份证号</label>
          <input v-model="userInfo.id_card" type="text" :disabled="!isEditing" />
        </div>
        <div class="settings__form-item">
          <label>所属片区</label>
          <input v-model="userInfo.region_name" type="text" disabled />
        </div>
        
        <div v-if="isAdmin && !isEditing">
          <button class="settings__button" @click="startEditing">编辑信息</button>
        </div>
        <div v-if="isEditing" class="button-group">
          <button class="settings__button" @click="saveUserInfo">保存</button>
          <button class="settings__button settings__button--secondary" @click="cancelEditing">取消</button>
        </div>
        
        <p v-if="!isAdmin" class="settings__note">
          💡 如需修改基本信息，请联系管理员
        </p>
      </div>
    </div>

    <!-- 密码修改 -->
    <div class="settings__card">
      <h2 class="settings__card-title">修改密码</h2>
      <div class="settings__form">
        <div class="settings__form-item">
          <label>当前密码</label>
          <input
            v-model="passwordForm.old_password"
            type="password"
            placeholder="请输入当前密码"
          />
        </div>
        <div class="settings__form-item">
          <label>新密码</label>
          <input
            v-model="passwordForm.new_password"
            type="password"
            placeholder="请输入新密码（6-20位）"
          />
        </div>
        <div class="settings__form-item">
          <label>确认新密码</label>
          <input
            v-model="passwordForm.confirm_password"
            type="password"
            placeholder="请再次输入新密码"
          />
        </div>
        <button class="settings__button" @click="handleChangePassword">
          修改密码
        </button>
      </div>
    </div>

    <!-- 主题设置 -->
    <div class="settings__card">
      <h2 class="settings__card-title">外观设置</h2>
      <div class="settings__form">
        <div class="settings__form-item">
          <label>主题模式</label>
          <select v-model="theme" @change="handleThemeChange">
            <option value="light">浅色模式</option>
            <option value="dark">深色模式</option>
            <option value="auto">跟随系统</option>
          </select>
        </div>
        <p class="settings__note">
          🎨 深色模式功能即将上线
        </p>
      </div>
    </div>

    <!-- 编辑用户模态框 -->
    <div v-if="showEditModal" class="modal" @click.self="closeEditModal">
      <div class="modal-content">
        <div class="modal-header">
          <h3>编辑用户信息</h3>
          <button class="modal-close" @click="closeEditModal">✕</button>
        </div>
        <div class="modal-body">
          <div class="settings__form-item">
            <label>邮箱</label>
            <input v-model="editingUser.mail" type="email" />
          </div>
          <div class="settings__form-item">
            <label>真实姓名</label>
            <input v-model="editingUser.real_name" type="text" />
          </div>
          <div class="settings__form-item">
            <label>身份证号</label>
            <input v-model="editingUser.idcard" type="text" />
          </div>
          <div class="settings__form-item">
            <label>角色</label>
            <select v-model="editingUser.role">
              <option value="resident">普通居民</option>
              <option value="area_admin">片区管理员</option>
              <option value="super_admin">超级管理员</option>
            </select>
          </div>
        </div>
        <div class="modal-footer">
          <button class="settings__button settings__button--secondary" @click="closeEditModal">取消</button>
          <button class="settings__button" @click="saveEditedUser">保存</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '@/composables/useAuth'
import userApi, { type UserInfo } from '@/services/api/user'
import { toast } from '@/utils/toast'
import { loading } from '@/utils/loading'

const router = useRouter()
const { user } = useAuth()

const isAdmin = computed(() => {
  const role = user.value?.role
  return role === 'super_admin' || role === 'area_admin'
})

const userInfo = ref<UserInfo>({
  user_id: 0,
  mail: '',
  real_name: '',
  id_card: '',
  region_id: 0,
  region_name: '',
  role: '',
  status: ''
})

const originalUserInfo = ref<UserInfo | null>(null)
const isEditing = ref(false)

const passwordForm = ref({
  old_password: '',
  new_password: '',
  confirm_password: ''
})

const theme = ref(localStorage.getItem('theme') || 'light')

// 用户管理相关
const userList = ref<any[]>([])
const searchKeyword = ref('')
const pagination = ref({
  page: 1,
  per_page: 10,
  total: 0,
  pages: 0,
  has_next: false,
  has_prev: false
})

const showEditModal = ref(false)
const editingUser = ref<any>({})

const getRoleClass = (role: string) => {
  const roleMap: Record<string, string> = {
    'super_admin': 'role-badge role-badge--super',
    'area_admin': 'role-badge role-badge--admin',
    'resident': 'role-badge role-badge--resident'
  }
  return roleMap[role] || 'role-badge'
}

const getRoleLabel = (role: string) => {
  const roleMap: Record<string, string> = {
    'super_admin': '超级管理员',
    'area_admin': '片区管理员',
    'resident': '普通居民'
  }
  return roleMap[role] || role
}

const getStatusLabel = (status: string) => {
  const statusMap: Record<string, string> = {
    'normal': '正常',
    'arrear': '欠费',
    'canceled': '已销户'
  }
  return statusMap[status] || status
}

const loadUserInfo = async () => {
  try {
    loading.show('加载用户信息...')
    const response = await userApi.getInfo()
    
    if (response.data && response.data) {
      userInfo.value = response.data
      originalUserInfo.value = { ...response.data }
    }
  } catch (error) {
    console.error('加载用户信息失败:', error)
    toast.error('加载用户信息失败')
  } finally {
    loading.hide()
  }
}

const startEditing = () => {
  originalUserInfo.value = { ...userInfo.value }
  isEditing.value = true
}

const cancelEditing = () => {
  if (originalUserInfo.value) {
    userInfo.value = { ...originalUserInfo.value }
  }
  isEditing.value = false
}

const saveUserInfo = async () => {
  try {
    loading.show('保存中...')
    
    // 只发送有值的字段
    const payload: any = {}
    
    if (userInfo.value.mail && userInfo.value.mail !== originalUserInfo.value?.mail) {
      payload.mail = userInfo.value.mail
    }
    
    if (userInfo.value.real_name && userInfo.value.real_name !== originalUserInfo.value?.real_name) {
      payload.real_name = userInfo.value.real_name
    }
    
    if (userInfo.value.id_card && userInfo.value.id_card !== originalUserInfo.value?.id_card) {
      payload.idcard = userInfo.value.id_card
    }
    
    // 如果没有任何修改
    if (Object.keys(payload).length === 0) {
      toast.warning('没有任何修改')
      loading.hide()
      return
    }
    
    await userApi.updateInfo(payload)
    toast.success('信息保存成功')
    isEditing.value = false
    // 重新加载用户信息
    await loadUserInfo()
  } catch (error: any) {
    console.error('保存用户信息失败:', error)
    const errorMsg = error.response?.data?.message || error.message || '保存失败'
    toast.error(errorMsg)
  } finally {
    loading.hide()
  }
}

const searchUsers = async () => {
  try {
    loading.show('搜索中...')
    const response = await userApi.getUserList({
      page: pagination.value.page,
      per_page: pagination.value.per_page,
      keyword: searchKeyword.value
    })
    
    if (response.data) {
      userList.value = response.data.users || []
      pagination.value = response.data.pagination || pagination.value
    }
  } catch (error: any) {
    toast.error(error.message || '搜索失败')
  } finally {
    loading.hide()
  }
}

const changePage = (page: number) => {
  pagination.value.page = page
  searchUsers()
}

const editUser = (user: any) => {
  editingUser.value = { ...user }
  showEditModal.value = true
}

const closeEditModal = () => {
  showEditModal.value = false
  editingUser.value = {}
}

const saveEditedUser = async () => {
  try {
    loading.show('保存中...')
    // 调用更新用户API
    await userApi.updateInfo({
      target_user_id: editingUser.value.user_id,
      mail: editingUser.value.mail,
      real_name: editingUser.value.real_name,
      idcard: editingUser.value.idcard
    })
    toast.success('用户信息更新成功')
    closeEditModal()
    searchUsers()
  } catch (error: any) {
    toast.error(error.message || '更新失败')
  } finally {
    loading.hide()
  }
}

const handleChangePassword = async () => {
  if (!passwordForm.value.old_password) {
    toast.warning('请输入当前密码')
    return
  }
  
  if (!passwordForm.value.new_password) {
    toast.warning('请输入新密码')
    return
  }
  
  if (passwordForm.value.new_password.length < 6 || passwordForm.value.new_password.length > 20) {
    toast.warning('新密码长度应为6-20位')
    return
  }
  
  if (passwordForm.value.new_password !== passwordForm.value.confirm_password) {
    toast.warning('两次输入的新密码不一致')
    return
  }

  try {
    loading.show('修改密码中...')
    await userApi.changePassword({
      old_password: passwordForm.value.old_password,
      new_password: passwordForm.value.new_password
    })
    
    toast.success('密码修改成功，请重新登录')
    localStorage.removeItem('auth_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user_info')
    
    setTimeout(() => {
      router.push('/login')
    }, 2000)
  } catch (error: any) {
    toast.error(error.message || '修改密码失败')
  } finally {
    loading.hide()
  }
}

const handleThemeChange = () => {
  localStorage.setItem('theme', theme.value)
  toast.info(`已切换到${theme.value === 'light' ? '浅色' : theme.value === 'dark' ? '深色' : '自动'}模式`)
  
  if (theme.value === 'dark') {
    toast.warning('深色模式即将上线，敬请期待')
  }
}

onMounted(() => {
  loadUserInfo()
  if (isAdmin.value) {
    searchUsers()
  }
})
</script>

<style scoped>
.settings {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
}

.settings__title {
  margin: 0 0 24px 0;
  font-size: 28px;
  font-weight: 700;
  color: var(--color-text-primary);
}

.settings__card {
  background: white;
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.settings__card-title {
  margin: 0 0 20px 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-primary);
  padding-bottom: 12px;
  border-bottom: 2px solid var(--color-border);
}

.user-management {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.user-search {
  display: flex;
  gap: 12px;
}

.user-search input {
  flex: 1;
  padding: 10px 12px;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  font-size: 14px;
}

.user-table {
  width: 100%;
  border-collapse: collapse;
}

.user-table th,
.user-table td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid var(--color-border);
}

.user-table th {
  font-weight: 600;
  color: var(--color-text-secondary);
  font-size: 14px;
}

.role-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.role-badge--super {
  background: #fef3c7;
  color: #92400e;
}

.role-badge--admin {
  background: #dbeafe;
  color: #1e40af;
}

.role-badge--resident {
  background: #e5e7eb;
  color: #374151;
}

.action-btn {
  padding: 6px 12px;
  border: 1px solid var(--color-primary);
  background: transparent;
  color: var(--color-primary);
  border-radius: 4px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.action-btn:hover {
  background: var(--color-primary);
  color: white;
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: var(--color-text-secondary);
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 12px;
  margin-top: 20px;
}

.pagination button {
  padding: 8px 16px;
  border: 1px solid var(--color-border);
  background: white;
  border-radius: 6px;
  cursor: pointer;
}

.pagination button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.settings__form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.settings__form-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.settings__form-item label {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-secondary);
}

.settings__form-item input,
.settings__form-item select {
  padding: 10px 12px;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s;
}

.settings__form-item input:disabled {
  background: #f5f5f5;
  cursor: not-allowed;
}

.settings__form-item input:focus,
.settings__form-item select:focus {
  border-color: var(--color-primary);
}

.button-group {
  display: flex;
  gap: 12px;
}

.settings__button {
  padding: 10px 24px;
  border: none;
  background: var(--color-primary);
  color: white;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: opacity 0.2s;
}

.settings__button:hover {
  opacity: 0.9;
}

.settings__button--secondary {
  background: #6b7280;
}

.settings__note {
  margin: 8px 0 0 0;
  font-size: 13px;
  color: var(--color-text-secondary);
}

/* 模态框样式 */
.modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 12px;
  width: 90%;
  max-width: 500px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid var(--color-border);
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.modal-close {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: var(--color-text-secondary);
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
}

.modal-close:hover {
  background: var(--color-hover);
}

.modal-body {
  padding: 24px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px;
  border-top: 1px solid var(--color-border);
}
</style>
