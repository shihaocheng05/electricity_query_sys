// 用户 API：登录、注册、获取与更新用户信息、角色变更等接口调用封装。
import {httpService} from '../http';
import type {ApiResponse} from "../http";

// 接口类型定义
export interface RegisterParams {
  mail: string;
  password: string;
  real_name?: string;
  idcard?: string;
  region_id?: number;
}

export interface LoginParams {
  mail: string;
  password: string;
}

export interface UpdateUserParams {
  mail?: string;
  password?: string;
  real_name?: string;
  phone?: string;
  idcard?: string;
  region_id?: number;
}

export interface BindMeterParams {
  target_user_id?: number;
  meter_code: string;
}

export interface UnbindMeterParams {
  target_user_id?: number;
  meter_id: number;
}

export interface ChangePasswordParams {
  old_password: string;
  new_password: string;
}

export interface GetUserListParams {
  page?: number;
  per_page?: number;
  region_id?: number;
  keyword?: string;
}

export interface RefreshTokenParams {
  refresh_token: string;
}

export interface SendResetCodeParams {
  mail: string;
}

export interface ResetPasswordParams {
  mail: string;
  code: string;
  new_password: string;
}

export interface UserInfo {
  user_id: number;
  mail: string;
  phone?: string;
  real_name?: string;
  id_card?: string;
  region_id?: number;
  region_name?: string;
  role: string;
  status: string;
  create_time?: string;
  update_time?: string;
}

export interface LoginResponse {
  token: string;
  refresh_token?: string;
  user_info: UserInfo;
}

export interface MeterInfo {
  meter_id: number;
  meter_code: string;
  meter_type: string;
  install_address: string;
  status: string;
  install_date?: string;
}

export interface PaginationResponse<T> {
  users: T[];
  pagination: {
    total: number;
    page: number;
    per_page: number;
    pages: number;
    has_next: boolean;
    has_prev: boolean;
  };
}

/**
 * 1. 用户注册
 * POST /api/v1/user/register
 */
export const register = (data: RegisterParams) => {
  return httpService.post<ApiResponse<UserInfo>>('/user/register', data);
};

/**
 * 2. 用户登录
 * POST /api/v1/user/login
 */
export const login = (data: LoginParams) => {
  return httpService.post<ApiResponse<LoginResponse>>('/user/login', data);
};

/**
 * 3. 刷新Token
 * POST /api/v1/user/refresh-token
 */
export const refreshToken = (data: RefreshTokenParams) => {
  return httpService.post<ApiResponse<{ token: string; refresh_token: string }>>('/user/refresh-token', data);
};

/**
 * 4. 获取用户信息
 * GET /api/v1/user/info
 */
export const getUserInfo = (params?: { user_id?: number }) => {
  return httpService.get<ApiResponse<UserInfo>>('/user/info', { params });
};

/**
 * 5. 修改用户信息
 * PUT /api/v1/user/update
 */
export const updateUser = (data: UpdateUserParams) => {
  return httpService.put<ApiResponse<UserInfo>>('/user/update', data);
};

/**
 * 6. 绑定电表
 * POST /api/v1/user/bind-meter
 */
export const bindMeter = (data: BindMeterParams) => {
  return httpService.post<ApiResponse<{
    success: boolean;
    msg: string;
    meter_info: MeterInfo;
  }>>('/user/bind-meter', data);
};

/**
 * 7. 解绑电表
 * POST /api/v1/user/unbind-meter
 */
export const unbindMeter = (data: UnbindMeterParams) => {
  return httpService.post<ApiResponse<{
    success: boolean;
    message: string;
    meter_info: {
      meter_code: string;
      meter_id: number;
    };
  }>>('/user/unbind-meter', data);
};

/**
 * 8. 获取用户电表列表
 * GET /api/v1/user/meters
 */
export const getUserMeters = () => {
  return httpService.get<ApiResponse<{
    success: boolean;
    total: number;
    meters: MeterInfo[];
  }>>('/user/meters');
};

/**
 * 9. 修改密码
 * POST /api/v1/user/change-password
 */
export const changePassword = (data: ChangePasswordParams) => {
  return httpService.post<ApiResponse<{
    success: boolean;
    message: string;
    user_id: number;
  }>>('/user/change-password', data);
};

/**
 * 10. 获取用户列表（管理员）
 * GET /api/v1/user/list
 */
export const getUserList = (params: GetUserListParams) => {
  return httpService.get<ApiResponse<PaginationResponse<UserInfo>>>('/user/list', { params });
};

/**
 * 11. 用户登出
 * POST /api/v1/user/logout
 */
export const logout = () => {
  return httpService.post<ApiResponse<{ user_id: number }>>('/user/logout');
};

/**
 * 12. 发送重置密码验证码
 * POST /api/v1/user/send-reset-code
 */
export const sendResetCode = (data: SendResetCodeParams) => {
  return httpService.post<ApiResponse<{
    success: boolean;
    message: string;
    email: string;
  }>>('/user/send-reset-code', data);
};

/**
 * 13. 重置密码
 * POST /api/v1/user/reset-password
 */
export const resetPassword = (data: ResetPasswordParams) => {
  return httpService.post<ApiResponse<{
    success: boolean;
    message: string;
    user_id: number;
  }>>('/user/reset-password', data);
};

// 默认导出所有API方法
export default {
  register,
  login,
  refreshToken,
  getUserInfo,
  updateUser,
  bindMeter,
  unbindMeter,
  getUserMeters,
  changePassword,
  getUserList,
  logout,
  sendResetCode,
  resetPassword,
  
  // 获取用户信息
  getInfo() {
    return httpService.get<ApiResponse<UserInfo>>('/user/info')
  },
  
  // 更新用户信息（别名）
  updateInfo(data: UpdateUserParams) {
    return httpService.put<ApiResponse<UserInfo>>('/user/update', data)
  },
};

