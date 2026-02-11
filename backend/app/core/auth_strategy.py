"""
认证策略模块 (Strategy Pattern)
实现可插拔的认证方式,支持本地认证和 LDAP 认证（预留）
"""
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Optional, TYPE_CHECKING
import re

from jose import JWTError, jwt
import bcrypt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.core.config import settings

# 使用 TYPE_CHECKING 避免循环导入
if TYPE_CHECKING:
    from app.models.user import User


class AuthenticationError(Exception):
    """认证异常基类"""
    pass


class InvalidCredentialsError(AuthenticationError):
    """无效凭证异常"""
    pass


class AccountLockedError(AuthenticationError):
    """账号锁定异常"""
    pass


class PasswordExpiredError(AuthenticationError):
    """密码过期异常"""
    pass


class AccountInactiveError(AuthenticationError):
    """账号未激活异常"""
    pass


class AuthStrategy(ABC):
    """
    认证策略抽象基类
    定义统一的认证接口，支持多种认证方式的可插拔实现
    """
    
    @abstractmethod
    async def authenticate(self, db: AsyncSession, username: str, password: str) -> "User":
        """
        认证用户
        
        Args:
            db: 数据库会话
            username: 用户名
            password: 密码
            
        Returns:
            User: 认证成功的用户对象
            
        Raises:
            AuthenticationError: 认证失败时抛出
        """
        pass
    
    @abstractmethod
    def create_access_token(self, user_id: int) -> str:
        """
        生成访问令牌
        
        Args:
            user_id: 用户ID
            
        Returns:
            str: JWT Token
        """
        pass
    
    @abstractmethod
    def verify_token(self, token: str) -> dict:
        """
        验证令牌
        
        Args:
            token: JWT Token
            
        Returns:
            dict: 令牌载荷数据
            
        Raises:
            JWTError: 令牌无效时抛出
        """
        pass


class LocalAuthStrategy(AuthStrategy):
    """
    本地认证策略（Phase 1 核心功能）
    
    功能特性：
    - 使用 Passlib + bcrypt 进行密码哈希
    - 使用 Python-Jose 生成 JWT Token（24 小时有效期）
    - 密码复杂度验证（大写、小写、数字、特殊字符中至少三种，长度>8位）
    - 登录失败锁定机制（连续 5 次错误锁定 30 分钟）
    - 密码定期修改策略（90 天强制修改）
    """
    
    def __init__(self):
        # JWT 配置
        self.SECRET_KEY = settings.SECRET_KEY
        self.ALGORITHM = settings.ALGORITHM
        self.ACCESS_TOKEN_EXPIRE_HOURS = settings.ACCESS_TOKEN_EXPIRE_HOURS
        
        # 密码策略配置
        self.PASSWORD_MIN_LENGTH = settings.PASSWORD_MIN_LENGTH
        self.PASSWORD_EXPIRE_DAYS = settings.PASSWORD_EXPIRE_DAYS
        self.MAX_LOGIN_ATTEMPTS = settings.MAX_LOGIN_ATTEMPTS
        self.ACCOUNT_LOCKOUT_MINUTES = settings.ACCOUNT_LOCKOUT_MINUTES
    
    async def authenticate(self, db: AsyncSession, username: str, password: str) -> "User":
        """
        本地认证实现
        
        认证流程：
        1. 查询用户
        2. 检查账号状态（锁定、激活状态）
        3. 验证密码
        4. 处理登录失败计数
        5. 检查密码是否过期
        """
        # 延迟导入避免循环依赖
        from app.models.user import User, UserStatus
        
        # 1. 查询用户
        result = await db.execute(
            select(User).where(User.username == username)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise InvalidCredentialsError("用户名或密码错误")
        
        # 2. 检查账号状态
        if user.status != UserStatus.ACTIVE:
            if user.status == UserStatus.PENDING:
                raise AccountInactiveError("账号待审核，请联系管理员")
            elif user.status == UserStatus.FROZEN:
                raise AccountInactiveError("账号已冻结，请联系管理员")
            elif user.status == UserStatus.REJECTED:
                raise AccountInactiveError("账号已被驳回")
        
        # 检查账号是否被锁定
        if user.is_account_locked():
            remaining_minutes = int((user.locked_until - datetime.utcnow()).total_seconds() / 60)
            raise AccountLockedError(f"账号已锁定，请在 {remaining_minutes} 分钟后重试")
        
        # 3. 验证密码
        if not self.verify_password(password, user.password_hash):
            # 登录失败，增加失败计数
            await self._handle_login_failure(db, user)
            raise InvalidCredentialsError("用户名或密码错误")
        
        # 4. 登录成功，重置失败计数
        await self._reset_login_attempts(db, user)
        
        # 5. 检查密码是否过期
        if user.is_password_expired(self.PASSWORD_EXPIRE_DAYS):
            raise PasswordExpiredError("密码已过期，请修改密码")
        
        # 更新最后登录时间
        await db.execute(
            update(User)
            .where(User.id == user.id)
            .values(last_login_at=datetime.utcnow())
        )
        await db.commit()
        
        return user
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        验证密码
        
        Args:
            plain_password: 明文密码
            hashed_password: 哈希密码
            
        Returns:
            bool: 密码是否匹配
        """
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )
    
    def hash_password(self, password: str) -> str:
        """
        哈希密码
        
        Args:
            password: 明文密码
            
        Returns:
            str: 哈希后的密码
        """
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def validate_password_complexity(self, password: str) -> tuple[bool, str]:
        """
        验证密码复杂度
        
        规则：大写、小写、数字、特殊字符中至少三种，长度>8位
        
        Args:
            password: 待验证的密码
            
        Returns:
            tuple[bool, str]: (是否通过, 错误信息)
        """
        if len(password) < self.PASSWORD_MIN_LENGTH:
            return False, f"密码长度必须大于 {self.PASSWORD_MIN_LENGTH} 位"
        
        # 检查字符类型
        has_upper = bool(re.search(r'[A-Z]', password))
        has_lower = bool(re.search(r'[a-z]', password))
        has_digit = bool(re.search(r'\d', password))
        has_special = bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password))
        
        complexity_count = sum([has_upper, has_lower, has_digit, has_special])
        
        if complexity_count < 3:
            return False, "密码必须包含大写字母、小写字母、数字、特殊字符中的至少三种"
        
        return True, ""
    
    async def _handle_login_failure(self, db: AsyncSession, user: "User"):
        """
        处理登录失败
        
        连续失败 5 次后锁定账号 30 分钟
        """
        from app.models.user import User
        
        new_attempts = user.failed_login_attempts + 1
        
        if new_attempts >= self.MAX_LOGIN_ATTEMPTS:
            # 锁定账号
            locked_until = datetime.utcnow() + timedelta(minutes=self.ACCOUNT_LOCKOUT_MINUTES)
            await db.execute(
                update(User)
                .where(User.id == user.id)
                .values(
                    failed_login_attempts=new_attempts,
                    locked_until=locked_until
                )
            )
        else:
            # 增加失败计数
            await db.execute(
                update(User)
                .where(User.id == user.id)
                .values(failed_login_attempts=new_attempts)
            )
        
        await db.commit()
    
    async def _reset_login_attempts(self, db: AsyncSession, user: "User"):
        """重置登录失败计数"""
        from app.models.user import User
        
        await db.execute(
            update(User)
            .where(User.id == user.id)
            .values(
                failed_login_attempts=0,
                locked_until=None
            )
        )
        await db.commit()
    
    def create_access_token(self, user_id: int) -> str:
        """
        生成 JWT Token
        
        Args:
            user_id: 用户ID
            
        Returns:
            str: JWT Token
        """
        expire = datetime.utcnow() + timedelta(hours=self.ACCESS_TOKEN_EXPIRE_HOURS)
        to_encode = {
            "sub": str(user_id),
            "exp": expire,
            "iat": datetime.utcnow()
        }
        encoded_jwt = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return encoded_jwt
    
    def verify_token(self, token: str) -> dict:
        """
        验证 JWT Token
        
        Args:
            token: JWT Token
            
        Returns:
            dict: 令牌载荷数据
            
        Raises:
            JWTError: 令牌无效时抛出
        """
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            return payload
        except JWTError as e:
            raise JWTError(f"Token 验证失败: {str(e)}")


class LDAPAuthStrategy(AuthStrategy):
    """
    LDAP 认证策略（Phase 2 预留）
    
    预留功能说明：
    - 集成公司 AD/LDAP 实现单点登录 (SSO)
    - 自动同步用户信息（姓名、部门、邮箱）
    - 支持 LDAP 组映射到系统权限
    
    实现计划：
    1. 使用 ldap3 库连接 LDAP 服务器
    2. 实现 LDAP Bind 验证
    3. 查询用户属性并同步到本地数据库
    4. 生成 JWT Token（复用 LocalAuthStrategy 的逻辑）
    
    配置要求：
    - LDAP_SERVER: LDAP 服务器地址
    - LDAP_BASE_DN: 基础 DN
    - LDAP_BIND_DN: 绑定 DN
    - LDAP_BIND_PASSWORD: 绑定密码
    """
    
    def __init__(self):
        # JWT 配置（复用本地认证的 Token 生成逻辑）
        self.SECRET_KEY = settings.SECRET_KEY
        self.ALGORITHM = settings.ALGORITHM
        self.ACCESS_TOKEN_EXPIRE_HOURS = settings.ACCESS_TOKEN_EXPIRE_HOURS
        
        # LDAP 配置
        self.LDAP_SERVER = settings.LDAP_SERVER
        self.LDAP_BASE_DN = settings.LDAP_BASE_DN
        self.LDAP_BIND_DN = settings.LDAP_BIND_DN
        self.LDAP_BIND_PASSWORD = settings.LDAP_BIND_PASSWORD
    
    async def authenticate(self, db: AsyncSession, username: str, password: str) -> "User":
        """
        LDAP 认证实现（预留）
        
        实现逻辑：
        1. 连接 LDAP 服务器
        2. 使用用户凭证进行 Bind 验证
        3. 查询用户属性（cn, mail, department）
        4. 同步或创建本地用户记录
        5. 返回用户对象
        """
        raise NotImplementedError(
            "LDAP 认证功能预留给 Phase 2 实现。"
            "需要配置 LDAP 服务器参数并实现 ldap3 集成逻辑。"
        )
    
    def create_access_token(self, user_id: int) -> str:
        """
        生成 JWT Token（复用本地认证逻辑）
        """
        expire = datetime.utcnow() + timedelta(hours=self.ACCESS_TOKEN_EXPIRE_HOURS)
        to_encode = {
            "sub": str(user_id),
            "exp": expire,
            "iat": datetime.utcnow()
        }
        encoded_jwt = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return encoded_jwt
    
    def verify_token(self, token: str) -> dict:
        """
        验证 JWT Token（复用本地认证逻辑）
        """
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            return payload
        except JWTError as e:
            raise JWTError(f"Token 验证失败: {str(e)}")


class AuthService:
    """
    统一认证服务
    
    根据用户类型和系统配置选择合适的认证策略：
    - 内部员工：优先使用 LocalAuthStrategy（预留 LDAP 切换逻辑）
    - 供应商：使用 LocalAuthStrategy + 图形验证码（验证码逻辑在 API 层实现）
    """
    
    def __init__(self):
        # 初始化认证策略
        self.local_strategy = LocalAuthStrategy()
        self.ldap_strategy = LDAPAuthStrategy()
    
    def get_strategy(self, user_type: str) -> AuthStrategy:
        """
        根据用户类型选择认证策略
        
        Args:
            user_type: 用户类型 (internal/supplier)
            
        Returns:
            AuthStrategy: 认证策略实例
        """
        if user_type == "internal":
            # 内部员工：检查是否启用 LDAP
            if settings.LDAP_ENABLED:
                return self.ldap_strategy
            else:
                return self.local_strategy
        elif user_type == "supplier":
            # 供应商：使用本地认证
            return self.local_strategy
        else:
            # 默认使用本地认证
            return self.local_strategy
    
    async def login(
        self,
        db: AsyncSession,
        username: str,
        password: str,
        user_type: str = "internal"
    ) -> dict:
        """
        统一登录接口
        
        Args:
            db: 数据库会话
            username: 用户名
            password: 密码
            user_type: 用户类型
            
        Returns:
            dict: 包含 access_token 和 user_info 的字典
            
        Raises:
            AuthenticationError: 认证失败时抛出
        """
        # 选择认证策略
        strategy = self.get_strategy(user_type)
        
        # 执行认证
        user = await strategy.authenticate(db, username, password)
        
        # 生成 Token
        access_token = strategy.create_access_token(user.id)
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_info": user.to_dict()
        }
    
    async def verify_token(self, token: str, db: AsyncSession) -> "User":
        """
        验证 Token 并返回用户对象
        
        Args:
            token: JWT Token
            db: 数据库会话
            
        Returns:
            User: 用户对象
            
        Raises:
            JWTError: Token 无效时抛出
        """
        from app.models.user import User, UserStatus
        
        # 使用本地策略验证 Token（LDAP 和本地使用相同的 JWT 逻辑）
        payload = self.local_strategy.verify_token(token)
        
        user_id = int(payload.get("sub"))
        
        # 查询用户
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise JWTError("用户不存在")
        
        if user.status != UserStatus.ACTIVE:
            raise JWTError("用户账号未激活")
        
        return user


# 创建全局认证服务实例
auth_service = AuthService()
