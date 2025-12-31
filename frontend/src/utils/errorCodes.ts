class ErrorCodes{
    code: number;
    message: string;
    errormsg: string;
    constructor(response:{code:number,message:string}){
        this.code=response.code;
        this.message=response.message;
        this.errormsg=`Error ${response.code}: ${response.message}`;
    }
}
export {ErrorCodes};