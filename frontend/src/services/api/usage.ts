// 用电数据模块 API 封装
import { httpService } from "../http";
import type { ApiResponse } from "../http";

export interface IoTUploadParams {
	meter_id: number;
	electricity: number;
	collect_time: string;
	voltage?: number;
	current?: number;
}

export interface UsageInfo {
	usage_id: number;
	meter_id: number;
	electricity: number;
	collect_time: string;
}

export interface AggregateParams {
	meter_id: number;
	usage_type: string; // DAY | MONTH
	target_date?: string;
}

export const iotUpload = (data: IoTUploadParams) => httpService.post<ApiResponse<UsageInfo>>("/usage/iot-upload", data);

export const aggregateUsage = (data: AggregateParams) => httpService.post<ApiResponse<any>>("/usage/aggregate", data);

export const queryUsage = (params?: any) => httpService.get<ApiResponse<any>>("/usage/query", { params });

export const manualInput = (data: IoTUploadParams) => httpService.post<ApiResponse<UsageInfo>>("/usage/manual-input", data);

export default { iotUpload, aggregateUsage, queryUsage, manualInput };
