// 账单 API：账单列表、明细查询、导出、支付与提醒相关接口封装。
import { httpService } from "../http";
import type { ApiResponse } from "../http";

export interface CreateBillParams {
	bill_month: string;
	meter_id: number;
}

export interface BillInfo {
	bill_id: number;
	meter_id: number;
	bill_no?: string;
	bill_month: string;
	total_usage: number;
	bill_amount: number;
	status: string;
	generate_time?: string;
	due_date?: string;
	payment_time?: string;
}

export interface PayBillParams {
	bill_id: number;
	payment_amount: number;
	payment_method: string;
	transaction_id?: string;
}

export interface BillsPaginationResponse<T> {
	bills: T[];
	pagination: {
		total: number;
		page: number;
		per_page: number;
		pages?: number;
		has_next?: boolean;
		has_prev?: boolean;
	};
}

export const createBill = (data: CreateBillParams) => httpService.post<ApiResponse<BillInfo>>("/bill/create", data);

export const payBill = (data: PayBillParams) => httpService.post<ApiResponse<BillInfo>>("/bill/pay", data);

export const queryBills = (params?: any) => httpService.get<ApiResponse<BillsPaginationResponse<BillInfo>>>("/bill/query", { params });

export const getBillDetail = (bill_id: number) => httpService.get<ApiResponse<BillInfo>>(`/bill/detail/${bill_id}`);

export const sendBillReminder = (bill_id: number) => httpService.post<ApiResponse<any>>(`/bill/reminder/${bill_id}`);

export const batchCreateBills = (data: { bill_month: string; region_id: number }) => httpService.post<ApiResponse<any>>("/bill/batch-create", data);

export default { createBill, payBill, queryBills, getBillDetail, sendBillReminder, batchCreateBills };
