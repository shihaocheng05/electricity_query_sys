// 系统管理模块 API 封装（电价策略、片区、用户角色、日志）
import { httpService } from "../http";
import type { ApiResponse } from "../http";

export interface PricePolicyCreateParams {
	policy_name: string;
	base_price: number;
	peak_price?: number;
	valley_price?: number;
	is_active: boolean;
}

export interface RegionCreateParams {
	region_name: string;
	region_code: string;
	description?: string;
}

// 价格政策相关
export const getPricePolicies = () => httpService.get<ApiResponse<any>>("/system/price-policy/list");

export const createPricePolicy = (data: any) => httpService.post<ApiResponse<any>>("/system/price-policy/create", data);

export const updatePricePolicy = (policyId: number, data: any) => httpService.put<ApiResponse<any>>("/system/price-policy/update", { ...data, policy_id: policyId });

export const deletePricePolicy = (policyId: number) => httpService.delete<ApiResponse<any>>(`/system/price-policy/${policyId}`);

// 片区相关
export const getRegions = () => httpService.get<ApiResponse<any>>("/system/region/list");

export const createRegion = (data: RegionCreateParams) => httpService.post<ApiResponse<any>>("/system/region/create", data);

export const updateRegion = (regionId: number, data: RegionCreateParams) => httpService.put<ApiResponse<any>>(`/system/region/${regionId}`, data);

export const deleteRegion = (regionId: number) => httpService.delete<ApiResponse<any>>(`/system/region/${regionId}`);

// 用户角色管理
export const updateUserRole = (data: { user_id: number; new_role: string }) => httpService.put<ApiResponse<any>>("/system/user/update-role", data);

// 系统日志
export const getSystemLogs = (params?: any) => httpService.get<ApiResponse<any>>("/system/logs", { params });

export default { 
	getPricePolicies,
	createPricePolicy, 
	updatePricePolicy, 
	deletePricePolicy,
	getRegions,
	createRegion, 
	updateRegion, 
	deleteRegion,
	updateUserRole, 
	getSystemLogs 
};
