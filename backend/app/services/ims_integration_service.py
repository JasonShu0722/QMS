"""
IMS 数据集成服务
IMS Integration Service - 与内部管理系统(IMS)对接，拉取质量数据
"""
import asyncio
from datetime import date, datetime, timedelta
from typing import Optional, Dict, List, Any
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.models.ims_sync_log import IMSSyncLog, SyncType, SyncStatus


class IMSIntegrationService:
    """
    IMS 集成服务类
    
    功能：
    - 使用 HTTPX 异步客户端从 IMS 系统拉取数据
    - 支持入库检验、成品产出、制程测试等多种数据类型
    - 实现错误处理和重试机制
    - 记录同步日志用于监控和追溯
    
    设计原则：
    - 异步非阻塞：使用 async/await 模式，避免阻塞主线程
    - 容错性：网络异常时自动重试，记录详细错误信息
    - 可追溯：每次同步操作都记录日志，便于问题排查
    """
    
    def __init__(self):
        """初始化 IMS 集成服务"""
        self.base_url = settings.IMS_BASE_URL
        self.api_key = settings.IMS_API_KEY
        self.timeout = settings.IMS_TIMEOUT
        
        # 配置 HTTPX 客户端
        self.client_config = {
            "timeout": httpx.Timeout(self.timeout),
            "headers": {
                "Content-Type": "application/json",
                "X-API-Key": self.api_key if self.api_key else "",
            },
            "follow_redirects": True,
        }
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        retry_count: int = 3
    ) -> Dict[str, Any]:
        """
        发起 HTTP 请求（带重试机制）
        
        Args:
            method: HTTP 方法 (GET, POST, etc.)
            endpoint: API 端点路径
            params: URL 查询参数
            json_data: JSON 请求体
            retry_count: 重试次数
            
        Returns:
            Dict[str, Any]: API 响应数据
            
        Raises:
            httpx.HTTPError: 网络请求失败
            ValueError: IMS 配置不完整
        """
        # 检查 IMS 配置
        if not self.base_url:
            raise ValueError("IMS_BASE_URL 未配置，请在 .env 文件中设置")
        
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        # 重试逻辑
        last_exception = None
        for attempt in range(retry_count):
            try:
                async with httpx.AsyncClient(**self.client_config) as client:
                    response = await client.request(
                        method=method,
                        url=url,
                        params=params,
                        json=json_data
                    )
                    
                    # 检查响应状态
                    response.raise_for_status()
                    
                    # 返回 JSON 数据
                    return response.json()
                    
            except httpx.HTTPError as e:
                last_exception = e
                print(f"IMS 请求失败 (尝试 {attempt + 1}/{retry_count}): {str(e)}")
                
                # 如果不是最后一次尝试，等待后重试
                if attempt < retry_count - 1:
                    await asyncio.sleep(2 ** attempt)  # 指数退避：2秒、4秒、8秒
                    continue
                else:
                    # 最后一次尝试失败，抛出异常
                    raise
        
        # 理论上不会到达这里，但为了类型检查
        raise last_exception
    
    async def fetch_incoming_inspection_data(
        self,
        db: AsyncSession,
        start_date: date,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        拉取入库检验数据
        
        用途：
        - 计算来料批次合格率 (2.4.1)
        - 计算物料上线不良 PPM (2.4.1)
        - 自动生成 SCAR 单 (2.5.1)
        
        Args:
            db: 数据库会话
            start_date: 开始日期
            end_date: 结束日期（默认为开始日期）
            
        Returns:
            Dict[str, Any]: 包含同步结果的字典
            {
                "success": bool,
                "records_count": int,
                "data": List[Dict],
                "error": Optional[str]
            }
        """
        if end_date is None:
            end_date = start_date
        
        # 创建同步日志
        sync_log = IMSSyncLog(
            sync_type=SyncType.INCOMING_INSPECTION,
            sync_date=start_date,
            status=SyncStatus.IN_PROGRESS,
            records_count=0,
            started_at=datetime.utcnow()
        )
        db.add(sync_log)
        await db.commit()
        await db.refresh(sync_log)
        
        try:
            # 调用 IMS API
            response_data = await self._make_request(
                method="GET",
                endpoint="/api/quality/incoming-inspection",
                params={
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                }
            )
            
            # 解析响应数据
            records = response_data.get("data", [])
            records_count = len(records)
            
            # 更新同步日志
            sync_log.status = SyncStatus.SUCCESS
            sync_log.records_count = records_count
            sync_log.completed_at = datetime.utcnow()
            await db.commit()
            
            print(f"✅ 入库检验数据同步成功: {records_count} 条记录")
            
            return {
                "success": True,
                "records_count": records_count,
                "data": records,
                "error": None
            }
            
        except Exception as e:
            # 记录错误
            error_message = f"入库检验数据同步失败: {str(e)}"
            sync_log.status = SyncStatus.FAILED
            sync_log.error_message = error_message
            sync_log.completed_at = datetime.utcnow()
            await db.commit()
            
            print(f"❌ {error_message}")
            
            return {
                "success": False,
                "records_count": 0,
                "data": [],
                "error": error_message
            }
    
    async def fetch_production_output_data(
        self,
        db: AsyncSession,
        start_date: date,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        拉取成品产出数据
        
        用途：
        - 计算制程不合格率 (2.4.1)
        - 计算 0KM 不良 PPM (2.4.1)
        - 试产数据自动抓取 (2.8.3)
        
        Args:
            db: 数据库会话
            start_date: 开始日期
            end_date: 结束日期（默认为开始日期）
            
        Returns:
            Dict[str, Any]: 包含同步结果的字典
        """
        if end_date is None:
            end_date = start_date
        
        # 创建同步日志
        sync_log = IMSSyncLog(
            sync_type=SyncType.PRODUCTION_OUTPUT,
            sync_date=start_date,
            status=SyncStatus.IN_PROGRESS,
            records_count=0,
            started_at=datetime.utcnow()
        )
        db.add(sync_log)
        await db.commit()
        await db.refresh(sync_log)
        
        try:
            # 调用 IMS API
            response_data = await self._make_request(
                method="GET",
                endpoint="/api/production/output",
                params={
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                }
            )
            
            # 解析响应数据
            records = response_data.get("data", [])
            records_count = len(records)
            
            # 更新同步日志
            sync_log.status = SyncStatus.SUCCESS
            sync_log.records_count = records_count
            sync_log.completed_at = datetime.utcnow()
            await db.commit()
            
            print(f"✅ 成品产出数据同步成功: {records_count} 条记录")
            
            return {
                "success": True,
                "records_count": records_count,
                "data": records,
                "error": None
            }
            
        except Exception as e:
            # 记录错误
            error_message = f"成品产出数据同步失败: {str(e)}"
            sync_log.status = SyncStatus.FAILED
            sync_log.error_message = error_message
            sync_log.completed_at = datetime.utcnow()
            await db.commit()
            
            print(f"❌ {error_message}")
            
            return {
                "success": False,
                "records_count": 0,
                "data": [],
                "error": error_message
            }
    
    async def fetch_process_test_data(
        self,
        db: AsyncSession,
        start_date: date,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        拉取制程测试数据
        
        用途：
        - 计算制程直通率 (FPY) (2.4.1)
        - 一次测试通过数、一次测试总数量
        
        Args:
            db: 数据库会话
            start_date: 开始日期
            end_date: 结束日期（默认为开始日期）
            
        Returns:
            Dict[str, Any]: 包含同步结果的字典
        """
        if end_date is None:
            end_date = start_date
        
        # 创建同步日志
        sync_log = IMSSyncLog(
            sync_type=SyncType.PROCESS_TEST,
            sync_date=start_date,
            status=SyncStatus.IN_PROGRESS,
            records_count=0,
            started_at=datetime.utcnow()
        )
        db.add(sync_log)
        await db.commit()
        await db.refresh(sync_log)
        
        try:
            # 调用 IMS API
            response_data = await self._make_request(
                method="GET",
                endpoint="/api/production/process-test",
                params={
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                }
            )
            
            # 解析响应数据
            records = response_data.get("data", [])
            records_count = len(records)
            
            # 更新同步日志
            sync_log.status = SyncStatus.SUCCESS
            sync_log.records_count = records_count
            sync_log.completed_at = datetime.utcnow()
            await db.commit()
            
            print(f"✅ 制程测试数据同步成功: {records_count} 条记录")
            
            return {
                "success": True,
                "records_count": records_count,
                "data": records,
                "error": None
            }
            
        except Exception as e:
            # 记录错误
            error_message = f"制程测试数据同步失败: {str(e)}"
            sync_log.status = SyncStatus.FAILED
            sync_log.error_message = error_message
            sync_log.completed_at = datetime.utcnow()
            await db.commit()
            
            print(f"❌ {error_message}")
            
            return {
                "success": False,
                "records_count": 0,
                "data": [],
                "error": error_message
            }
    
    async def sync_all_data(
        self,
        db: AsyncSession,
        target_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        同步所有类型的数据（用于 Celery 定时任务）
        
        Args:
            db: 数据库会话
            target_date: 目标日期（默认为昨天）
            
        Returns:
            Dict[str, Any]: 包含所有同步结果的汇总
        """
        if target_date is None:
            # 默认同步昨天的数据
            target_date = date.today() - timedelta(days=1)
        
        print(f"🔄 开始同步 IMS 数据: {target_date}")
        
        results = {
            "date": target_date.isoformat(),
            "started_at": datetime.utcnow().isoformat(),
            "incoming_inspection": None,
            "production_output": None,
            "process_test": None,
            "overall_success": False
        }
        
        # 1. 同步入库检验数据
        incoming_result = await self.fetch_incoming_inspection_data(
            db=db,
            start_date=target_date
        )
        results["incoming_inspection"] = incoming_result
        
        # 2. 同步成品产出数据
        output_result = await self.fetch_production_output_data(
            db=db,
            start_date=target_date
        )
        results["production_output"] = output_result
        
        # 3. 同步制程测试数据
        test_result = await self.fetch_process_test_data(
            db=db,
            start_date=target_date
        )
        results["process_test"] = test_result
        
        # 判断整体是否成功
        results["overall_success"] = all([
            incoming_result["success"],
            output_result["success"],
            test_result["success"]
        ])
        
        results["completed_at"] = datetime.utcnow().isoformat()
        
        if results["overall_success"]:
            print(f"✅ IMS 数据同步完成: {target_date}")
        else:
            print(f"⚠️ IMS 数据同步部分失败: {target_date}")
        
        return results
    
    async def get_sync_history(
        self,
        db: AsyncSession,
        sync_type: Optional[SyncType] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 50
    ) -> List[IMSSyncLog]:
        """
        查询同步历史记录
        
        Args:
            db: 数据库会话
            sync_type: 同步类型（可选）
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）
            limit: 返回记录数量限制
            
        Returns:
            List[IMSSyncLog]: 同步日志列表
        """
        query = select(IMSSyncLog)
        
        # 添加筛选条件
        if sync_type:
            query = query.where(IMSSyncLog.sync_type == sync_type)
        
        if start_date:
            query = query.where(IMSSyncLog.sync_date >= start_date)
        
        if end_date:
            query = query.where(IMSSyncLog.sync_date <= end_date)
        
        # 按创建时间倒序排列
        query = query.order_by(IMSSyncLog.created_at.desc()).limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()


# 创建全局 IMS 集成服务实例
ims_integration_service = IMSIntegrationService()
