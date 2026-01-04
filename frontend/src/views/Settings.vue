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

    <!-- 电表管理 -->
    <div class="settings__card">
      <h2 class="settings__card-title">电表管理</h2>
      <div class="meter-management">
        <!-- 已绑定电表列表 -->
        <div class="meter-section">
          <h3>📊 我的电表</h3>
          <div v-if="meterList.length > 0" class="meter-list">
            <div v-for="meter in meterList" :key="meter.meter_id" class="meter-item">
              <div class="meter-info">
                <div class="meter-header">
                  <div class="meter-code">{{ meter.meter_code }}</div>
                  <span class="meter-id">ID: {{ meter.meter_id }}</span>
                </div>
                <div class="meter-details">
                  <span class="meter-address">📍 {{ meter.install_address }}</span>
                  <span class="meter-status" :class="'meter-status--' + meter.status.toLowerCase()">
                    {{ getMeterStatusLabel(meter.status) }}
                  </span>
                </div>
              </div>
              <button class="action-btn action-btn--danger" @click="handleUnbindMeter(meter)">
                解绑
              </button>
            </div>
          </div>
          <div v-else class="empty-state">
            暂无绑定的电表
          </div>
        </div>

        <!-- 管理员：安装新电表 -->
        <div v-if="isAdmin" class="install-meter-form meter-section">
          <h3>🔧 安装新电表（管理员）</h3>
          <p class="form-hint">💡 为用户安装全新的电表，安装后将自动绑定到该用户</p>
          <div class="settings__form-item">
            <label>目标用户ID</label>
            <input
              v-model.number="installMeterForm.target_user_id"
              type="number"
              placeholder="输入用户ID"
            />
          </div>
          <div class="settings__form-item">
            <label>安装地址</label>
            <input
              v-model="installMeterForm.install_address"
              type="text"
              placeholder="例如：北京市朝阳区XX路XX号"
            />
          </div>
          <button class="settings__button" @click="handleInstallMeter">
            安装电表
          </button>
        </div>

        <!-- 空闲电表列表（仅管理员）-->
        <div v-if="isAdmin" class="available-meters-section meter-section">
          <h3>📋 空闲电表列表</h3>
          <p class="form-hint">💡 显示本片区所有未分配给用户的电表</p>
          <button class="settings__button settings__button--secondary" @click="loadAvailableMeters" style="margin-bottom: 16px;">
            刷新列表
          </button>
          <div v-if="availableMeterList.length > 0" class="meter-list">
            <div v-for="meter in availableMeterList" :key="meter.meter_id" class="meter-item">
              <div class="meter-info">
                <div class="meter-header">
                  <div class="meter-code">{{ meter.meter_code }}</div>
                  <span class="meter-id">ID: {{ meter.meter_id }}</span>
                </div>
                <div class="meter-details">
                  <span class="meter-address">📍 {{ meter.install_address }}</span>
                  <span class="meter-type">类型: {{ meter.meter_type }}</span>
                  <span class="meter-time">安装: {{ meter.install_time }}</span>
                </div>
              </div>
              <div class="meter-actions">
                <button class="action-btn action-btn--copy" @click="copyMeterCode(meter.meter_code)">
                  📋 复制编号
                </button>
                <button class="action-btn action-btn--info" @click="copyMeterId(meter.meter_id)">
                  🔢 复制ID
                </button>
              </div>
            </div>
          </div>
          <div v-else class="empty-state">
            暂无空闲电表
          </div>
        </div>

        <!-- 绑定未分配的电表 -->
        <div class="bind-meter-form meter-section">
          <h3>🔄 电表更换/过户</h3>
          <p class="form-hint">💡 绑定一个尚未分配给任何用户的电表（用于电表更换或过户场景）</p>
          <div class="settings__form-item">
            <label>电表编号</label>
            <input
              v-model="bindMeterForm.meter_code"
              type="text"
              placeholder="例如：BJ-CY-S-202601011200-001"
            />
          </div>
          <button class="settings__button" @click="handleBindMeter">
            绑定电表
          </button>
        </div>
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
import meterApi from '@/services/api/meter'
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

// 电表管理相关
const meterList = ref<any[]>([])
const bindMeterForm = ref({
  meter_code: ''
})
const installMeterForm = ref({
  target_user_id: null as number | null,
  install_address: ''
})

const availableMeterList = ref<any[]>([])

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
  editingUser.value = { 
    ...user,
    idcard: user.id_card // 转换字段名
  }
  showEditModal.value = true
}

const closeEditModal = () => {
  showEditModal.value = false
  editingUser.value = {}
}

const saveEditedUser = async () => {
  try {
    loading.show('保存中...')
    
    // 构建请求payload
    const payload: any = {
      target_user_id: editingUser.value.user_id,
      mail: editingUser.value.mail,
      real_name: editingUser.value.real_name
    }
    
    // 身份证如果包含星号说明是脱敏数据，不发送
    if (editingUser.value.idcard && !editingUser.value.idcard.includes('*')) {
      payload.idcard = editingUser.value.idcard
    }
    
    // 调用更新用户API
    await userApi.updateInfo(payload)
    toast.success('用户信息更新成功')
    closeEditModal()
    searchUsers()
  } catch (error: any) {
    const errorMsg = error.response?.data?.message || error.message || '更新失败'
    toast.error(errorMsg)
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

// 获取电表状态标签
const getMeterStatusLabel = (status: string) => {
  const statusMap: Record<string, string> = {
    'NORMAL': '正常',
    'ABNORMAL': '异常',
    'OFFLINE': '离线',
    'MAINTAIN': '维护中'
  }
  return statusMap[status] || status
}

// 加载用户电表列表
const loadUserMeters = async () => {
  try {
    console.log('准备获取电表列表...')
    const response = await userApi.getUserMeters()
    console.log('电表列表原始响应:', JSON.stringify(response, null, 2))
    if (response && response.data) {
      console.log('response.data:', response.data)
      // 后端返回格式: { success: true, message: "获取成功", data: { total: 1, meters: [...] } }
      const metersData = response.data
      console.log('metersData:', metersData)
      if (metersData && metersData.meters) {
        console.log('找到电表数据:', metersData.meters)
        meterList.value = metersData.meters
      } else if (Array.isArray(metersData)) {
        console.log('电表数据是数组:', metersData)
        meterList.value = metersData
      } else {
        console.log('未找到电表数据')
      }
    }
    console.log('最终meterList:', meterList.value)
  } catch (error: any) {
    console.error('加载电表列表失败:', error)
    console.error('错误详情:', error.response)
    toast.error('加载电表列表失败')
  }
}

// 绑定电表
const handleBindMeter = async () => {
  if (!bindMeterForm.value.meter_code) {
    toast.warning('请输入电表编号')
    return
  }

  try {
    loading.show('绑定中...')
    await userApi.bindMeter({
      target_user_id: userInfo.value.user_id,
      meter_code: bindMeterForm.value.meter_code
    })
    toast.success('电表绑定成功')
    bindMeterForm.value.meter_code = ''
    // 重新加载电表列表
    await loadUserMeters()
  } catch (error: any) {
    console.error('绑定电表失败:', error)
    const errorMsg = error.response?.data?.message || error.message || '绑定失败'
    toast.error(errorMsg)
  } finally {
    loading.hide()
  }
}

// 解绑电表
const handleUnbindMeter = async (meter: any) => {
  if (!confirm(`确定要解绑电表 ${meter.meter_code} 吗？`)) {
    return
  }

  try {
    loading.show('解绑中...')
    await userApi.unbindMeter({
      target_user_id: userInfo.value.user_id,
      meter_id: meter.meter_id
    })
    toast.success('电表解绑成功')
    // 重新加载电表列表
    await loadUserMeters()
  } catch (error: any) {
    console.error('解绑电表失败:', error)
    const errorMsg = error.response?.data?.message || error.message || '解绑失败'
    toast.error(errorMsg)
  } finally {
    loading.hide()
  }
}

// 安装新电表（管理员）
const handleInstallMeter = async () => {
  if (!installMeterForm.value.target_user_id) {
    toast.warning('请输入目标用户ID')
    return
  }
  
  if (!installMeterForm.value.install_address) {
    toast.warning('请输入安装地址')
    return
  }

  try {
    loading.show('安装中...')
    const response = await meterApi.installMeter({
      target_user_id: installMeterForm.value.target_user_id,
      region_id: userInfo.value.region_id || 1,
      install_address: installMeterForm.value.install_address
    })
    
    if (response.data) {
      const meterInfo = response.data.meter_info || response.data
      toast.success(`电表安装成功！电表编号：${meterInfo.meter_code}`)
      // 清空表单
      installMeterForm.value.target_user_id = null
      installMeterForm.value.install_address = ''
      // 重新加载电表列表
      await loadUserMeters()
    }
  } catch (error: any) {
    console.error('安装电表失败:', error)
    const errorMsg = error.response?.data?.message || error.message || '安装失败'
    toast.error(errorMsg)
  } finally {
    loading.hide()
  }
}

// 加载空闲电表列表
const loadAvailableMeters = async () => {
  if (!isAdmin.value) return
  
  try {
    loading.show('加载中...')
    const response = await meterApi.getAvailableMeters({
      page: 1,
      per_page: 50
    })
    
    if (response.data && response.data.meters) {
      availableMeterList.value = response.data.meters
      toast.success(`找到 ${response.data.meters.length} 个空闲电表`)
    }
  } catch (error: any) {
    console.error('加载空闲电表失败:', error)
    toast.error('加载空闲电表失败')
  } finally {
    loading.hide()
  }
}

// 复制电表编号
const copyMeterCode = async (meterCode: string) => {
  try {
    await navigator.clipboard.writeText(meterCode)
    toast.success('电表编号已复制到剪贴板')
  } catch (error) {
    // 降级方案
    const textArea = document.createElement('textarea')
    textArea.value = meterCode
    document.body.appendChild(textArea)
    textArea.select()
    document.execCommand('copy')
    document.body.removeChild(textArea)
    toast.success('电表编号已复制')
  }
}

// 复制电表ID
const copyMeterId = async (meterId: number) => {
  try {
    await navigator.clipboard.writeText(meterId.toString())
    toast.success('电表ID已复制到剪贴板')
  } catch (error) {
    // 降级方案
    const textArea = document.createElement('textarea')
    textArea.value = meterId.toString()
    document.body.appendChild(textArea)
    textArea.select()
    document.execCommand('copy')
    document.body.removeChild(textArea)
    toast.success('电表编号已复制')
  }
}

onMounted(() => {
  loadUserInfo()
  loadUserMeters()
  if (isAdmin.value) {
    searchUsers()
    loadAvailableMeters()
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

/* 电表管理样式 */
.meter-management {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.meter-section {
  padding: 20px;
  border-radius: 8px;
  background: #ffffff;
  border: 1px solid var(--color-border);
}

.meter-section h3 {
  margin: 0 0 16px 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.meter-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.meter-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  background: #f9fafb;
  transition: all 0.2s;
}

.meter-item:hover {
  border-color: var(--color-primary);
  background: #f0f9ff;
}

.meter-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.meter-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.meter-code {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.meter-id {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  background: #e0e7ff;
  color: #4338ca;
}

.meter-actions {
  display: flex;
  gap: 8px;
}

.meter-details {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 14px;
}

.meter-address {
  color: var(--color-text-secondary);
}

.meter-status {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.meter-status--normal {
  background: #d1fae5;
  color: #065f46;
}

.meter-status--abnormal {
  background: #fee2e2;
  color: #991b1b;
}

.meter-status--offline {
  background: #e5e7eb;
  color: #374151;
}

.meter-status--maintain {
  background: #fef3c7;
  color: #92400e;
}

.install-meter-form {
  border: 2px solid var(--color-primary) !important;
  background: #f0f9ff !important;
}

.install-meter-form h3 {
  color: var(--color-primary) !important;
}

.bind-meter-form {
  border: 2px dashed #94a3b8 !important;
  background: #f8fafc !important;
}

.bind-meter-form h3 {
  color: #475569 !important;
}

.available-meters-section {
  background: #fefce8 !important;
  border: 2px solid #facc15 !important;
}

.available-meters-section h3 {
  color: #854d0e !important;
}

.meter-type {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  background: #dbeafe;
  color: #1e40af;
}

.meter-time {
  font-size: 12px;
  color: #6b7280;
}

.action-btn--copy {
  background: #3b82f6;
}

.action-btn--copy:hover {
  background: #2563eb;
}

.action-btn--info {
  background: #8b5cf6;
}

.action-btn--info:hover {
  background: #7c3aed;
}

.settings__button--secondary {
  background: #6b7280;
}

.settings__button--secondary:hover {
  background: #4b5563;
}

.form-hint {
  margin: 0 0 16px 0;
  font-size: 13px;
  color: var(--color-text-secondary);
}

.action-btn--danger {
  background: #dc2626;
}

.action-btn--danger:hover {
  background: #b91c1c;
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
