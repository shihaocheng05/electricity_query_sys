// 电表 API：电表绑定、状态查询、读数录入与电表列表获取封装。
import { httpService } from "../http";
import type {ApiResponse} from "../http";

export interface InstallParams{
    target_user_id:number;
    region_id:number;
    current_region_id:number;
    install_address:string;
}

export interface MeterInfo{
    meter_id:number;
    meter_code:string;
    user_id:number;
    meter_type:string;
    install_address:string;
    status:string;
    install_date:string;
}

export interface MeterStatusInfo{
    meter_id:number;
    status:string;
}

export interface AddRecordParams{
    meter_id:number;
    record_type:string;
    operator:string;
    content:string;
    attach_img?:string;
}

export interface MeterRecordInfo{
    record_id:number;
    meter_id:number;
    record_type:string;
    operator:string;
    content:string;
    create_time:string;
}

export interface RepairParams{
    meter_id:number;
    fault_address:string;
    fault_description:string;
    attach_img:string;
}

export interface RepairInfo{
    repair_id:number;
    meter_id:number;
    status:string;
}

export interface ValidateReadingParams{
    meter_id:number;
    new_reading:number;
    reading_time:string;
}

export interface ValidateInfo{
    meter_id:number;
    old_reading:number;
    new_reading:number;
    usage:number;
}

export interface PaginationResponse<T> {
  meters: T[];
  pagination: {
    total: number;
    page: number;
    per_page: number;
    pages: number;
    has_next: boolean;
    has_prev: boolean;
  };
}

export interface MeterRecordPaginationResponse<T> {
  records: T[];
  pagination: {
    total: number;
    page: number;
    per_page: number; 
    pages: number;
    has_next: boolean;
    has_prev: boolean;
  };
}

export const installMeter=(data:InstallParams)=>{
    return httpService.post<ApiResponse<MeterInfo>>('/meter/install',data);
}

export const updateMeterStatus=(data:MeterStatusInfo)=>{
    return httpService.put<ApiResponse<MeterStatusInfo>>('/meter/update-status',data);
}

export const addMeterRecord=(data:AddRecordParams)=>{
    return httpService.post<ApiResponse<MeterRecordInfo>>('/meter/add-record',data);
}

export const repairMeter=(data:RepairParams)=>{
    return httpService.post<ApiResponse<RepairInfo>>('/meter/repair',data);
}

export const validateReading=(data:ValidateReadingParams)=>{
    return httpService.post<ApiResponse<ValidateInfo>>('/meter/validate-reading',data);
}

export const getMeterList=()=>{
    return httpService.get<ApiResponse<PaginationResponse<MeterInfo>>>('/meter/query');
}

export const getMeterRecords=(meter_id:number)=>{
    return httpService.get<ApiResponse<MeterRecordPaginationResponse<MeterRecordInfo>>>(`/meter/records/${meter_id}`);
}

export default {
    installMeter,
    updateMeterStatus,
    addMeterRecord,
    repairMeter,
    validateReading,
    getMeterList,
    getMeterRecords
};