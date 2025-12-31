// 通知模块 API 封装
import { httpService } from "../http";
import type { ApiResponse } from "../http";

export interface CreateNotificationParams {
	notice_type: string;
	target_type: string;
	target_ids: number[];
	title: string;
	content: string;
	send_channel?: string;
	send_time?: string;
	is_batch?: boolean;
	related_id?: number;
}

export interface NotificationInfo {
	notification_id: number;
	notice_type: string;
	title: string;
	status: string;
}

export interface NotificationQueryParams {
	user_id?: number;
	notify_type?: string;
	status?: string;
	is_unread_only?: boolean;
	page?: number;
	per_page?: number;
}

export const createNotification = (data: CreateNotificationParams) => httpService.post<ApiResponse<NotificationInfo>>("/notification/create", data);

export const sendNotification = (data: { notification_id?: number; batch_id?: string }) => httpService.post<ApiResponse<any>>("/notification/send", data);

export const queryNotifications = (params?: NotificationQueryParams) => httpService.get<ApiResponse<any>>("/notification/query", { params });

export const notificationStatistics = (params?: { notify_type?: string; start_date?: string; end_date?: string }) =>
	httpService.get<ApiResponse<any>>("/notification/statistics", { params });

export const updateNotificationStatus = (data: { notification_id: number; action: string; user_id?: number }) =>
	httpService.put<ApiResponse<any>>("/notification/update-status", data);

export const notificationApi = { 
	createNotification, 
	sendNotification, 
	queryNotifications, 
	notificationStatistics, 
	updateNotificationStatus 
};

export default notificationApi;
