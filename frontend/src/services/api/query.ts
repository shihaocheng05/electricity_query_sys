// 查询分析模块 API 封装
import { httpService } from "../http";
import type { ApiResponse } from "../http";

export interface AnalyzeUserParams {
	user_id?: number;
	analysis_period?: string; // day|month|year
	compare_period?: boolean;
}

export interface AnalyzeRegionParams {
	region_id: number;
	analysis_period?: string;
	compare_period?: boolean;
}

export interface ExportDataParams {
	export_type: string;
	start_date?: string;
	end_date?: string;
	region_id?: number;
	format?: string;
}

export interface ExportDataResponse {
	download_url?: string;
	file_name?: string;
	filename?: string;
	export_time?: string;
}

export const analyzeUser = (params: AnalyzeUserParams) => {
	return httpService.get<ApiResponse<any>>('/query/analyze/user', { params });
};

export const analyzeRegion = (params?: AnalyzeRegionParams) => httpService.get<ApiResponse<any>>("/query/analyze/region", { params });

export const ranking = (params?: { region_id?: number; ranking_type?: string; time_range?: string; limit?: number }) =>
	httpService.get<ApiResponse<any>>("/query/ranking", { params });

export const statisticsSummary = (params?: { scope?: string; scope_id?: number }) =>
	httpService.get<ApiResponse<any>>("/query/statistics/summary", { params });

export const exportData = (params: ExportDataParams) => {
	return httpService.get<ApiResponse<ExportDataResponse>>('/query/export', { params });
};

export default { analyzeUser, analyzeRegion, ranking, statisticsSummary, exportData };
