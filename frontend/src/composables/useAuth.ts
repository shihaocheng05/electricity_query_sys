// useAuth：封装登录态管理（读取/刷新 token、权限判断、退出登录）。
import { useAuthStore } from '@/stores';
import type { LoginParams } from '@/services/api/user';
import { computed } from 'vue';

// 验证 JWT Token 是否过期
function isTokenExpired(token: string): boolean {
    try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        const exp = payload.exp * 1000; // 转换为毫秒
        return Date.now() >= exp;
    } catch (e) {
        console.error('Token解析失败:', e);
        return true; // 解析失败视为过期
    }
}

export function useAuth() {
    const authStore = useAuthStore();
    
    const initAuth = () => {
        console.log('initAuth 被调用')
        const token = localStorage.getItem('auth_token');
        const userInfo = localStorage.getItem('user_info');
        console.log('localStorage token:', token)
        console.log('localStorage userInfo:', userInfo)
        
        // 检查 token 是否存在且未过期
        if(token && !isTokenExpired(token)) {
            authStore.login(token);
            if(userInfo) {
                try {
                    authStore.user = JSON.parse(userInfo);
                    console.log('恢复用户信息成功，角色:', authStore.user?.role)
                } catch(e) {
                    console.error('解析用户信息失败:', e);
                }
            }
        } else if(token) {
            // Token 已过期，清除本地存储
            console.log('Token已过期，清除登录状态');
            localStorage.removeItem('auth_token');
            localStorage.removeItem('refresh_token');
            localStorage.removeItem('user_info');
            authStore.isLoggedIn = false;
            authStore.token = null;
            authStore.user = null;
        }
        console.log('initAuth 完成，isLoggedIn:', authStore.isLoggedIn)
    };

    const isLoggedIn = computed(() => authStore.isLoggedIn);
    const token = computed(() => authStore.token);
    const user = computed(() => authStore.user);
    
    const signIn=async (credentials: LoginParams) => {      //封装异步逻辑
        return await authStore.signIn(credentials);
    }

    const logout=async () => {
        await authStore.logout();
    };

    return {
        initAuth,
        isLoggedIn,
        token,
        user,
        signIn,
        logout,
    };
}