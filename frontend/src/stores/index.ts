// 状态管理入口：应用级状态（登录态、主题、全局通知、查询条件等）统一管理说明与后续实现位置（建议使用 Pinia）。
import { createPinia,defineStore } from 'pinia';
import { login as apiLogin, logout as apiLogout, getUserInfo as apiGetUserInfo } from '@/services/api/user';
import type { LoginParams, UserInfo, LoginResponse } from '@/services/api/user';
import type { ApiResponse } from '@/services/http';
import { ref } from 'vue';

const pinia = createPinia();

export const useAuthStore=defineStore("auth",()=>{
    // 登录态相关状态
    const isLoggedIn = ref(false);
    const token=ref<string|null>(null);
    const user=ref<UserInfo|null>(null);  // 完整用户信息

    // 设置 token（同步 setter）,同步更新登录状态
    function login(newToken:string){
        isLoggedIn.value=true;
        token.value=newToken;
    }

    // 异步登录：调用后端 API，保存 token 到 state 与 localStorage
    async function signIn(credentials: LoginParams) {
        const res = await apiLogin(credentials);
        // 注意：http 拦截器已经返回了 response.data，所以 res 就是后端返回的数据
        // 后端格式：{ success: true, message: '...', data: { token, refresh_token, user_info } }
        if (res && (res as any).success && (res as any).data?.token) {
            const t = (res as any).data.token;
            isLoggedIn.value = true;
            token.value = t;
            localStorage.setItem('auth_token', t);
            
            if ((res as any).data.refresh_token) {
                localStorage.setItem('refresh_token', (res as any).data.refresh_token);
            }
            
            // 使用登录返回的用户信息
            if ((res as any).data.user_info) {
                user.value = (res as any).data.user_info;
                localStorage.setItem('user_info', JSON.stringify((res as any).data.user_info));
            }
        }
        return res;
    }

    async function logout(){
        try{
            await apiLogout();
        }catch(e){
            // 忽略后端登出错误，继续本地清理
        }
        isLoggedIn.value=false;
        token.value=null;
        localStorage.removeItem('auth_token');
        localStorage.removeItem('refresh_token');
    }
    
    return { isLoggedIn, token, user, login, signIn, logout };
})

export const useAppStore=defineStore("app",()=>{
    // 全局应用状态（主题、通知等）
    const theme=ref<"light"|"dark">("light");   // 主题，默认 light
    function setTheme(newTheme:"light"|"dark"){
        theme.value=newTheme;
        document.documentElement.setAttribute("data-theme",newTheme);
    }
    return { theme, setTheme };
})